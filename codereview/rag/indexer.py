import logging
from dataclasses import dataclass
from pathlib import PurePosixPath

log = logging.getLogger(__name__)

CODE_SUFFIXES = {".py", ".pyi", ".ts", ".tsx", ".js", ".jsx"}
MAX_INDEX_BYTES = 200_000
CODE_WINDOW, CODE_OVERLAP = 60, 10
STYLE_WINDOW, STYLE_OVERLAP = 100, 10


@dataclass(frozen=True)
class Chunk:
    source_type: str  # code | style | pr_comment
    path: str
    start_line: int
    end_line: int
    content: str


def window_chunks(text: str, size: int, overlap: int) -> list[tuple[int, int, str]]:
    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) must be smaller than size ({size})")
    lines = text.splitlines()
    if not lines:
        return []
    step = size - overlap
    out: list[tuple[int, int, str]] = []
    start = 0
    while start < len(lines):
        seg = lines[start : start + size]
        out.append((start + 1, start + len(seg), "\n".join(seg)))
        if start + size >= len(lines):
            break
        start += step
    return out


def is_code_path(path: str) -> bool:
    return PurePosixPath(path).suffix in CODE_SUFFIXES


def is_style_path(path: str) -> bool:
    p = PurePosixPath(path)
    name = p.name.upper()
    if name in {"README.MD", "CONTRIBUTING.MD"} or name.startswith("STYLEGUIDE"):
        return True
    return p.parts[:1] == ("docs",) and p.suffix == ".md"


def chunk_file(path: str, text: str) -> list[Chunk]:
    if is_code_path(path):
        wins, st = window_chunks(text, CODE_WINDOW, CODE_OVERLAP), "code"
    elif is_style_path(path):
        wins, st = window_chunks(text, STYLE_WINDOW, STYLE_OVERLAP), "style"
    else:
        return []
    return [Chunk(st, path, s, e, c) for s, e, c in wins if c.strip()]


def comment_chunk(comment: dict) -> Chunk | None:
    body = (comment.get("body") or "").strip()
    if not body:
        return None
    path = comment.get("path") or ""
    return Chunk("pr_comment", path, 0, 0, f"{path}: {body}"[:4000])
