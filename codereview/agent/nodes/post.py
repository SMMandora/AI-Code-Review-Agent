import logging
import re
import time

from codereview.agent.cost import total_cost_usd
from codereview.agent.dedup import apply_dedup
from codereview.agent.state import AgentDeps, Finding, ReviewState
from codereview.github.client import GitHubError

log = logging.getLogger(__name__)


def _suggestion_block(code: str) -> str:
    longest = max((len(m.group(0)) for m in re.finditer(r"`+", code)), default=0)
    marker = "`" * max(3, longest + 1)
    return f"{marker}suggestion\n{code}\n{marker}"


def format_comment(f: Finding) -> str:
    body = f"**[{f.severity}] {f.category}**: {f.message}"
    if f.suggestion:
        body += "\n" + _suggestion_block(f.suggestion)
    return body


def compose_review_body(state: ReviewState, summary_only: list[Finding], cost_usd: float) -> str:
    pr = state["pr"]
    cfg = state["config"]
    findings = state.get("findings", [])
    errors = state.get("errors", [])
    wall_s = time.monotonic() - state.get("started_monotonic", time.monotonic())
    counts = {s: sum(1 for f in findings if f.severity == s) for s in ("high", "medium", "low")}

    lines = ["## 🤖 AI Code Review", ""]
    lines.append(
        f"Model `{cfg.model}` · cost ${cost_usd:.4f} · {wall_s:.1f}s · "
        f"{counts['high']} high / {counts['medium']} medium / {counts['low']} low"
    )
    if errors:
        failed = ", ".join(sorted(e.node for e in errors))
        lines += ["", f"⚠️ Checks that failed to run: {failed}"]
    if cfg.warnings:
        lines += [""] + [f"⚠️ Config: {w}" for w in cfg.warnings]
    if summary_only:
        lines += ["", "Findings without an inline anchor:"]
        lines += [
            f"- `{f.path}:{f.line}` **[{f.severity}] {f.category}**: {f.message}"
            for f in summary_only
        ]
    lines += ["", MARKER_LINE(pr.head_sha), "", "*Reply `/review again` to re-run this review.*"]
    return "\n".join(lines)


def MARKER_LINE(sha: str) -> str:
    from codereview.agent.nodes.fetch import MARKER

    return MARKER.format(sha=sha)


def make_post_node(deps: AgentDeps):
    async def node(state: ReviewState) -> dict:
        cfg = state["config"]
        pr = state["pr"]
        pairs = [(u.input_tokens, u.output_tokens) for u in state.get("usage", [])]
        cost = total_cost_usd(cfg.model, pairs)

        if cost > deps.settings.cost_ceiling_usd:
            log.error(
                "actual cost $%.4f exceeds ceiling $%.2f — NOT posting review for pr=%d",
                cost, deps.settings.cost_ceiling_usd, pr.number,
            )
            return {"skip_reason": "cost_exceeded"}

        errors = state.get("errors", [])
        findings = state.get("findings", [])
        if errors and not findings:
            return {"skip_reason": "all_checks_failed"}

        dd = apply_dedup(
            findings, state.get("diff_files", []), threshold=cfg.severity_threshold
        )
        inline, summary_only = dd.inline, dd.summary_only
        body = compose_review_body(state, summary_only, cost)
        comments = [
            {"path": f.path, "line": f.line, "side": "RIGHT", "body": format_comment(f)}
            for f in inline
        ]
        try:
            await deps.gh.create_review(pr.number, pr.head_sha, body, comments)
        except GitHubError as exc:
            if exc.status == 422 and comments:
                log.warning("422 posting inline comments, retrying summary-only: %s", exc)
                note = "\n\n*(Inline comments could not be anchored to the diff.)*"
                try:
                    await deps.gh.create_review(pr.number, pr.head_sha, body + note, [])
                except GitHubError:
                    log.error("summary-only retry also failed for pr=%d", pr.number)
                    raise
                comments = []
            else:
                raise
        return {
            "posted": True,
            "comments_posted": len(comments),
            "findings_total": len(findings),
        }

    return node
