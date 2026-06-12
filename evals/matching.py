import re
from dataclasses import dataclass

from codereview.agent.state import Finding


@dataclass(frozen=True)
class Expected:
    path: str
    line_start: int
    line_end: int
    category: str
    pattern: str  # regex, case-insensitive, searched in message + suggestion


def match_findings(
    produced: list[Finding], expected: list[Expected]
) -> tuple[list[tuple[Expected, Finding]], list[Expected], list[Finding]]:
    """Greedy 1:1 matching (spec §12). Returns (matched, missed_expected, extra_produced)."""
    matched: list[tuple[Expected, Finding]] = []
    used: set[int] = set()
    missed: list[Expected] = []
    for ex in expected:
        hit = None
        for i, f in enumerate(produced):
            if i in used:
                continue
            text = f"{f.message} {f.suggestion or ''}"
            if (
                f.path == ex.path
                and ex.line_start <= f.line <= ex.line_end
                and f.category == ex.category
                and re.search(ex.pattern, text, re.IGNORECASE)
            ):
                hit = i
                break
        if hit is None:
            missed.append(ex)
        else:
            used.add(hit)
            matched.append((ex, produced[hit]))
    extra = [f for i, f in enumerate(produced) if i not in used]
    return matched, missed, extra
