import logging
from pathlib import PurePosixPath

from codereview.agent.cost import preflight_estimate_usd
from codereview.agent.state import AgentDeps, PRMeta, ReviewState
from codereview.diff import parse_diff
from codereview.repo_config import RepoConfig

log = logging.getLogger(__name__)

MARKER = "<!-- ai-code-review:v1 sha={sha} -->"
CODE_SUFFIXES = {".py", ".pyi", ".ts", ".tsx", ".js", ".jsx"}
MAX_FULL_FILES = 10
MAX_FILE_BYTES = 50_000


def make_fetch_node(deps: AgentDeps):
    async def node(state: ReviewState) -> dict:
        job = state["job"]
        s = deps.settings
        head = job.head_sha or await deps.gh.resolve_pr_head(job.pr_number)

        if not job.force:
            if await deps.reviews.has_completed(s.github_repo, job.pr_number, head):
                return {"skip_reason": "already_reviewed"}
            marker = MARKER.format(sha=head)
            for rv in await deps.gh.list_reviews(job.pr_number):
                if marker in (rv.get("body") or ""):
                    return {"skip_reason": "already_reviewed"}

        pr_json = await deps.gh.get_pr(job.pr_number)
        pr = PRMeta(
            number=job.pr_number,
            title=pr_json.get("title") or "",
            body=pr_json.get("body") or "",
            author=(pr_json.get("user") or {}).get("login", ""),
            head_sha=head,
            base_ref=(pr_json.get("base") or {}).get("ref", ""),
            default_branch=((pr_json.get("base") or {}).get("repo") or {}).get(
                "default_branch", "main"
            ),
        )

        if deps.config_loader is not None:
            config: RepoConfig = await deps.config_loader(pr.default_branch)
        else:
            config = RepoConfig(model=s.default_model)

        diff_text = await deps.gh.get_pr_diff(job.pr_number)
        files = [
            f
            for f in parse_diff(diff_text)
            if not f.is_binary and not f.is_deleted and not config.skips(f.path)
        ]
        if not files:
            return {"pr": pr, "config": config, "skip_reason": "empty_diff"}

        est = preflight_estimate_usd(config.model, sum(len(f.raw) for f in files))
        if est * 1.3 > s.cost_ceiling_usd:
            log.error(
                "pre-flight cost estimate $%.4f (x1.3) exceeds ceiling $%.2f — skipping pr=%d",
                est, s.cost_ceiling_usd, job.pr_number,
            )
            return {"pr": pr, "config": config, "skip_reason": "cost_preflight"}

        contents: dict[str, str] = {}
        for f in sorted(files, key=lambda x: len(x.raw), reverse=True)[:MAX_FULL_FILES]:
            if PurePosixPath(f.path).suffix in CODE_SUFFIXES:
                text = await deps.gh.get_file(f.path, head)
                if text is not None and len(text) <= MAX_FILE_BYTES:
                    contents[f.path] = text

        return {"pr": pr, "config": config, "diff_files": files, "file_contents": contents}

    return node
