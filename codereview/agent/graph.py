import logging
import time

from langgraph.graph import END, START, StateGraph

from codereview.agent.cost import total_cost_usd
from codereview.agent.nodes.checks import make_check_node
from codereview.agent.nodes.context import make_context_node
from codereview.agent.nodes.fetch import make_fetch_node
from codereview.agent.nodes.post import make_post_node
from codereview.agent.state import CATEGORIES, AgentDeps, ReviewState
from codereview.stores import ReviewRecord
from codereview.worker import ReviewJob

log = logging.getLogger(__name__)

SKIP_STATUS = {
    "already_reviewed": "skipped",
    "empty_diff": "skipped",
    "cost_preflight": "cost_exceeded",
    "cost_exceeded": "cost_exceeded",
    "all_checks_failed": "failed",
}


def route_after_fetch(state: ReviewState) -> str:
    return "skip" if state.get("skip_reason") else "go"


def build_graph(deps: AgentDeps):
    g = StateGraph(ReviewState)
    g.add_node("fetch", make_fetch_node(deps))
    g.add_node("embed_context", make_context_node(deps))
    for category in CATEGORIES:
        g.add_node(f"check_{category}", make_check_node(category, deps))
    g.add_node("post", make_post_node(deps))

    g.add_edge(START, "fetch")
    g.add_conditional_edges("fetch", route_after_fetch, {"skip": END, "go": "embed_context"})
    for category in CATEGORIES:
        g.add_edge("embed_context", f"check_{category}")  # fan-out: parallel superstep
    g.add_edge([f"check_{category}" for category in CATEGORIES], "post")  # fan-in barrier
    g.add_edge("post", END)
    return g.compile()


def make_run_review(deps: AgentDeps):
    graph = build_graph(deps)

    async def run_review(job: ReviewJob) -> None:
        t0 = time.monotonic()
        try:
            final: ReviewState = await graph.ainvoke({"job": job, "started_monotonic": t0})
        except Exception as exc:
            log.exception("review pipeline crashed for pr=%d", job.pr_number)
            await deps.reviews.record(
                ReviewRecord(
                    repo=deps.settings.github_repo,
                    pr_number=job.pr_number,
                    head_sha=job.head_sha or "",
                    status="failed",
                    trigger=job.trigger,
                    model=deps.settings.default_model,
                    duration_ms=int((time.monotonic() - t0) * 1000),
                    error=repr(exc)[:500],
                )
            )
            return

        cfg = final.get("config")
        model = cfg.model if cfg else deps.settings.default_model
        usage = final.get("usage", [])
        cost = total_cost_usd(model, [(u.input_tokens, u.output_tokens) for u in usage])
        skip = final.get("skip_reason")
        status = "completed" if final.get("posted") else SKIP_STATUS.get(skip or "", "failed")
        pr = final.get("pr")
        errors = final.get("errors", [])
        await deps.reviews.record(
            ReviewRecord(
                repo=deps.settings.github_repo,
                pr_number=job.pr_number,
                head_sha=pr.head_sha if pr else (job.head_sha or ""),
                status=status,
                trigger=job.trigger,
                model=model,
                findings_total=final.get("findings_total", len(final.get("findings", []))),
                comments_posted=final.get("comments_posted", 0),
                input_tokens=sum(u.input_tokens for u in usage),
                output_tokens=sum(u.output_tokens for u in usage),
                cost_usd=round(cost, 4),
                duration_ms=int((time.monotonic() - t0) * 1000),
                error="; ".join(e.error for e in errors)[:500] or None,
            )
        )
        log.info(
            "review done pr=%d status=%s cost=$%.4f ms=%d",
            job.pr_number, status, cost, int((time.monotonic() - t0) * 1000),
        )

    return run_review
