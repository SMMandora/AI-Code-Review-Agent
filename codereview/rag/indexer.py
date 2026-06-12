import io
import logging
import tarfile
from collections.abc import Callable
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


def extract_tarball(tar_bytes: bytes) -> list[tuple[str, str]]:
    """(path, text) pairs from a GitHub tarball; strips the root dir; size-capped."""
    out: list[tuple[str, str]] = []
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tf:
        for member in tf.getmembers():
            if not member.isreg() or member.size > MAX_INDEX_BYTES:
                continue
            parts = member.name.split("/", 1)
            if len(parts) != 2 or not parts[1]:
                continue
            f = tf.extractfile(member)
            if f is None:
                continue
            out.append((parts[1], f.read().decode("utf-8", errors="replace")))
    return out


class Indexer:
    def __init__(self, store, embedder, skip: Callable[[str], bool] | None = None) -> None:
        self.store = store
        self.embedder = embedder
        self.skip = skip or (lambda path: False)

    async def _index_chunks(self, chunks: list[Chunk], commit_sha: str) -> int:
        if not chunks:
            return 0
        embeddings = await self.embedder.embed_documents([c.content for c in chunks])
        await self.store.upsert(chunks, embeddings, commit_sha)
        return len(chunks)

    async def seed_from_tarball(self, tar_bytes: bytes, commit_sha: str, repo: str) -> int:
        await self.store.wipe()
        chunks: list[Chunk] = []
        for path, text in extract_tarball(tar_bytes):
            if self.skip(path):
                continue
            chunks.extend(chunk_file(path, text))
        n = await self._index_chunks(chunks, commit_sha)
        await self.store.set_index_state(repo, commit_sha)
        log.info("seeded %d chunks at %s", n, commit_sha)
        return n

    async def index_pr_comments(self, comments: list[dict], commit_sha: str) -> int:
        chunks = [c for c in (comment_chunk(cm) for cm in comments) if c is not None]
        return await self._index_chunks(chunks, commit_sha)

    async def reindex_paths(
        self, gh, changed: list[str], removed: list[str], after_sha: str, repo: str
    ) -> int:
        await self.store.delete_paths(list(changed) + list(removed))
        chunks: list[Chunk] = []
        for path in changed:
            if self.skip(path) or not (is_code_path(path) or is_style_path(path)):
                continue
            text = await gh.get_file(path, after_sha)
            if text is not None:
                chunks.extend(chunk_file(path, text))
        n = await self._index_chunks(chunks, after_sha)
        await self.store.set_index_state(repo, after_sha)
        log.info("reindexed %d chunks at %s", n, after_sha)
        return n
