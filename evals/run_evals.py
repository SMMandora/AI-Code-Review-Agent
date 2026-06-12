"""Eval runner + release gate (spec §12). Live Claude calls — needs ANTHROPIC_API_KEY.

Usage:
    python -m evals.run_evals [--pr pr_007] [--limit N] [--model claude-sonnet-4-6]

Exit code 0 iff findings-match rate >= 80%.
"""

import argparse
import asyncio
import sys

from anthropic import AsyncAnthropic

from codereview.agent.cost import total_cost_usd
from codereview.agent.dedup import apply_dedup
from codereview.agent.nodes.checks import make_check_node
from codereview.agent.state import CATEGORIES, AgentDeps
from codereview.repo_config import RepoConfig
from codereview.settings import Settings
from evals.loader import EvalFixture, load_all
from evals.matching import match_findings

GATE = 0.80


async def run_fixture(fx: EvalFixture, deps: AgentDeps, model: str):
    state = {
        "pr": fx.pr,
        "diff_files": fx.diff_files,
        "file_contents": fx.file_contents,
        "config": RepoConfig(model=model),
        "context": fx.context,
    }
    results = await asyncio.gather(*(make_check_node(c, deps)(state) for c in CATEGORIES))
    findings, usage = [], []
    for r in results:
        findings.extend(r.get("findings", []))
        usage.extend(r.get("usage", []))
    dd = apply_dedup(findings, fx.diff_files, threshold="low")
    produced = dd.inline + dd.summary_only
    matched, missed, extra = match_findings(produced, fx.expected)
    cost = total_cost_usd(model, [(u.input_tokens, u.output_tokens) for u in usage])
    return matched, missed, extra, cost


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--model")
    args = ap.parse_args()

    settings = Settings()
    if not settings.anthropic_api_key:
        print("FAIL: set ANTHROPIC_API_KEY in .env")
        return 2
    model = args.model or settings.default_model
    deps = AgentDeps(
        settings=settings, gh=None, reviews=None,
        anthropic=AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=60.0, max_retries=1),
    )

    fixtures = load_all()
    if args.pr:
        fixtures = [f for f in fixtures if f.name == args.pr]
    if args.limit:
        fixtures = fixtures[: args.limit]
    if not fixtures:
        print(f"FAIL: no fixtures matched (pr={args.pr!r})")
        return 2

    total_expected = total_matched = 0
    total_extra = total_cost = 0.0
    for fx in fixtures:
        matched, missed, extra, cost = await run_fixture(fx, deps, model)
        total_expected += len(matched) + len(missed)
        total_matched += len(matched)
        total_extra += len(extra)
        total_cost += cost
        flag = "OK " if not missed else "MISS"
        print(
            f"{flag} {fx.name}: {len(matched)}/{len(matched) + len(missed)} matched, "
            f"{len(extra)} extra, ${cost:.4f}"
        )
        for ex in missed:
            print(
                f"     missed: {ex.path}:{ex.line_start}-{ex.line_end} "
                f"[{ex.category}] /{ex.pattern}/"
            )

    rate = (total_matched / total_expected) if total_expected else 1.0
    print(
        f"\nfindings match: {total_matched}/{total_expected} = {rate:.1%} "
        f"(gate {GATE:.0%}) | extra findings: {int(total_extra)} | cost ${total_cost:.2f}"
    )
    if rate >= GATE:
        print("GATE PASSED")
        return 0
    print("GATE FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
