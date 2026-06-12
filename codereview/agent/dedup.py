from dataclasses import dataclass, field
from difflib import SequenceMatcher

from codereview.agent.state import Finding
from codereview.diff import DiffFile, snap_line

SEV_RANK = {"high": 0, "medium": 1, "low": 2}
CATEGORY_RANK = {"security": 0, "correctness": 1, "test_coverage": 2, "style": 3}
SIMILARITY = 0.7
LINE_WINDOW = 2


@dataclass
class DedupResult:
    inline: list[Finding] = field(default_factory=list)
    summary_only: list[Finding] = field(default_factory=list)


def _quality_key(f: Finding) -> tuple:
    return (SEV_RANK[f.severity], CATEGORY_RANK.get(f.category, 9), -len(f.message))


def _order_key(f: Finding) -> tuple:
    return (SEV_RANK[f.severity], CATEGORY_RANK.get(f.category, 9), f.path, f.line)


def _is_duplicate(a: Finding, b: Finding) -> bool:
    if a.path != b.path or abs(a.line - b.line) > LINE_WINDOW:
        return False
    if a.category == b.category:
        return True
    return SequenceMatcher(None, a.message, b.message).ratio() >= SIMILARITY


def apply_dedup(
    findings: list[Finding],
    diff_files: list[DiffFile],
    threshold: str,
    max_inline: int = 7,
) -> DedupResult:
    """Spec §10 dedup node: threshold -> snap -> group -> cap."""
    result = DedupResult()
    eligible = [f for f in findings if SEV_RANK[f.severity] <= SEV_RANK[threshold]]

    by_path = {df.path: df for df in diff_files}
    anchored: list[Finding] = []
    for f in eligible:
        df = by_path.get(f.path)
        snapped = snap_line(df, f.line) if df is not None else None
        if snapped is None:
            result.summary_only.append(f)
        else:
            anchored.append(f.model_copy(update={"line": snapped}))

    kept: list[Finding] = []
    for f in sorted(anchored, key=_quality_key):  # best first, so kept wins
        if not any(_is_duplicate(f, k) for k in kept):
            kept.append(f)

    ordered = sorted(kept, key=_order_key)
    result.inline = ordered[:max_inline]
    result.summary_only.extend(ordered[max_inline:])
    return result
