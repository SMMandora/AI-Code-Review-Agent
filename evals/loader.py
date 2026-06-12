from dataclasses import dataclass, field
from pathlib import Path

import yaml

from codereview.agent.state import PRMeta, RetrievedContext, Snippet
from codereview.diff import DiffFile, parse_diff
from evals.matching import Expected

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@dataclass
class EvalFixture:
    name: str
    pr: PRMeta
    diff_files: list[DiffFile]
    file_contents: dict[str, str]
    context: RetrievedContext
    expected: list[Expected]
    notes: str = ""
    _dir: Path = field(default=Path("."), repr=False)


def load_fixture(path: Path) -> EvalFixture:
    meta = yaml.safe_load((path / "meta.yml").read_text(encoding="utf-8"))
    diff_files = parse_diff((path / "diff.patch").read_text(encoding="utf-8"))
    number = int(path.name.split("_")[1])
    pr = PRMeta(
        number=number, title=meta["title"], body=meta.get("body", ""),
        author="fixture", head_sha=f"eval{number:03d}", base_ref="main",
        default_branch="main",
    )
    contents: dict[str, str] = {}
    files_dir = path / "files"
    if files_dir.is_dir():
        for f in files_dir.rglob("*"):
            if f.is_file():
                contents[f.relative_to(files_dir).as_posix()] = f.read_text(encoding="utf-8")
    ctx = RetrievedContext()
    ctx_dir = path / "context"
    if ctx_dir.is_dir():
        for f in sorted(ctx_dir.glob("*.txt")):
            ctx.global_snippets.append(
                Snippet("style", f.name, 1, 1, f.read_text(encoding="utf-8"))
            )
    raw = yaml.safe_load((path / "expected.yml").read_text(encoding="utf-8")) or {}
    expected = [Expected(**e) for e in raw.get("expected") or []]
    return EvalFixture(
        name=path.name, pr=pr, diff_files=diff_files, file_contents=contents,
        context=ctx, expected=expected, notes=meta.get("notes", ""), _dir=path,
    )


def load_all() -> list[EvalFixture]:
    fixtures = []
    for p in sorted(FIXTURES_DIR.iterdir()):
        if not (p.is_dir() and p.name.startswith("pr_")):
            continue
        try:
            fixtures.append(load_fixture(p))
        except Exception as exc:
            raise RuntimeError(f"fixture {p.name} failed to load: {exc}") from exc
    return fixtures
