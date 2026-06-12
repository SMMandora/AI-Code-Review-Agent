from dataclasses import dataclass

from unidiff import PatchSet


@dataclass(frozen=True)
class DiffFile:
    path: str
    is_new: bool
    is_deleted: bool
    is_binary: bool
    commentable: frozenset[int]  # NEW-side line numbers valid for inline comments
    added_text: str
    raw: str  # the file's portion of the unified diff


def parse_diff(diff_text: str) -> list[DiffFile]:
    out: list[DiffFile] = []
    for pf in PatchSet(diff_text):
        commentable: set[int] = set()
        added: list[str] = []
        for hunk in pf:
            for line in hunk:
                if (line.is_added or line.is_context) and line.target_line_no:
                    commentable.add(line.target_line_no)
                if line.is_added:
                    added.append(line.value)
        out.append(
            DiffFile(
                path=pf.path,
                is_new=pf.is_added_file,
                is_deleted=pf.is_removed_file,
                is_binary=pf.is_binary_file,
                commentable=frozenset(commentable),
                added_text="".join(added),
                raw=str(pf),
            )
        )
    return out


def snap_line(df: DiffFile, line: int, max_dist: int = 5) -> int | None:
    """Nearest commentable NEW-side line within max_dist, else None (spec §8)."""
    if line in df.commentable:
        return line
    best = min(df.commentable, key=lambda c: abs(c - line), default=None)
    if best is not None and abs(best - line) <= max_dist:
        return best
    return None
