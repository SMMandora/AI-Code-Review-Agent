from dataclasses import dataclass
from pathlib import Path

import yaml

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@dataclass(frozen=True)
class RegressionCase:
    check: str
    name: str
    description: str
    pr_title: str
    pr_body: str
    diff: str
    injected_marker: str | None
    planted_bug: dict | None  # {path, line, pattern}
    must_still_find: bool


def load_cases(check: str | None = None) -> list[RegressionCase]:
    cases = []
    for check_dir in sorted(FIXTURES_DIR.iterdir()):
        if not check_dir.is_dir() or (check and check_dir.name != check):
            continue
        for f in sorted(check_dir.glob("case_*.yml")):
            d = yaml.safe_load(f.read_text(encoding="utf-8"))
            cases.append(RegressionCase(
                check=check_dir.name,
                name=d["name"],
                description=d.get("description", ""),
                pr_title=d.get("pr_title", "Update"),
                pr_body=d.get("pr_body", ""),
                diff=d["diff"],
                injected_marker=d.get("injected_marker"),
                planted_bug=d.get("planted_bug"),
                must_still_find=bool(d.get("must_still_find", False)),
            ))
    return cases
