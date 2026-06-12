import logging
import time

from codereview.agent.prompting import render_system, render_user
from codereview.agent.state import (
    AgentDeps,
    CheckError,
    CheckResult,
    Finding,
    NodeUsage,
    ReviewState,
)

log = logging.getLogger(__name__)

RETRY_SUFFIX = (
    "\n\nYour previous reply failed schema validation. "
    "Respond with data matching the schema exactly."
)


class CheckParseError(Exception):
    pass


async def call_model(client, model: str, system: str, user: str, max_tokens: int = 4000):
    """One structured-output call with a single corrective retry (spec §10)."""
    content = user
    last_exc: Exception | None = None
    for _attempt in (1, 2):
        try:
            resp = await client.messages.parse(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": content}],
                thinking={"type": "adaptive"},
                output_format=CheckResult,
            )
        except Exception as exc:
            last_exc = exc
            content = user + RETRY_SUFFIX
            continue
        if getattr(resp, "parsed_output", None) is not None:
            return resp.parsed_output, resp.usage
        content = user + RETRY_SUFFIX
    raise CheckParseError(f"model call failed twice: {last_exc!r}")


def make_check_node(category: str, deps: AgentDeps):
    async def node(state: ReviewState) -> dict:
        t0 = time.monotonic()
        cfg = state["config"]

        def elapsed_ms() -> int:
            return int((time.monotonic() - t0) * 1000)

        system = render_system(deps.settings.github_repo, category, cfg.custom_rules)
        user = render_user(state["pr"], state["diff_files"], state.get("context"), category)
        try:
            result, usage = await call_model(deps.anthropic, cfg.model, system, user)
        except Exception as exc:
            log.exception("check node %s failed", category)
            return {
                "errors": [CheckError(category, repr(exc)[:300])],
                "usage": [NodeUsage(category, 0, 0, elapsed_ms())],
            }
        findings = [
            Finding(**{**mf.model_dump(), "message": mf.message[:600]}, category=category)
            for mf in result.findings
        ]
        # cache read/creation tokens (if any) are billed as input — count them (spec §10)
        in_tokens = (
            usage.input_tokens
            + (getattr(usage, "cache_creation_input_tokens", 0) or 0)
            + (getattr(usage, "cache_read_input_tokens", 0) or 0)
        )
        nu = NodeUsage(category, in_tokens, usage.output_tokens, elapsed_ms())
        log.info(
            "check=%s findings=%d in_tokens=%d out_tokens=%d ms=%d",
            category, len(findings), nu.input_tokens, nu.output_tokens, nu.duration_ms,
        )
        return {"findings": findings, "usage": [nu]}

    node.__name__ = f"check_{category}"
    return node
