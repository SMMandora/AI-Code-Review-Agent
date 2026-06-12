import logging

from codereview.agent.state import Snippet
from codereview.db import Database
from codereview.rag.indexer import Chunk

log = logging.getLogger(__name__)


class ChunkStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def upsert(
        self, chunks: list[Chunk], embeddings: list[list[float]], commit_sha: str
    ) -> None:
        rows = [
            (c.source_type, c.path, c.start_line, c.end_line, c.content, emb, commit_sha)
            for c, emb in zip(chunks, embeddings, strict=True)
        ]
        async with self._db.pool.acquire() as conn:
            await conn.executemany(
                "INSERT INTO chunks (source_type, path, start_line, end_line, content, "
                "embedding, commit_sha) VALUES ($1,$2,$3,$4,$5,$6,$7)",
                rows,
            )

    async def delete_paths(self, paths: list[str]) -> None:
        if not paths:
            return
        async with self._db.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM chunks WHERE path = ANY($1) AND source_type IN ('code','style')",
                paths,
            )

    async def wipe(self) -> None:
        async with self._db.pool.acquire() as conn:
            await conn.execute("TRUNCATE chunks")

    async def count(self) -> int:
        async with self._db.pool.acquire() as conn:
            return await conn.fetchval("SELECT count(*) FROM chunks")

    async def search(
        self,
        embedding: list[float],
        source_type: str,
        k: int,
        exclude_path: str | None = None,
    ) -> list[Snippet]:
        async with self._db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT source_type, path, start_line, end_line, content FROM chunks "
                "WHERE source_type = $2 AND ($3::text IS NULL OR path <> $3) "
                "ORDER BY embedding <=> $1 LIMIT $4",
                embedding, source_type, exclude_path, k,
            )
        return [
            Snippet(r["source_type"], r["path"], r["start_line"], r["end_line"], r["content"])
            for r in rows
        ]

    async def set_index_state(self, repo: str, sha: str) -> None:
        async with self._db.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO index_state (repo, last_indexed_sha, indexed_at) "
                "VALUES ($1, $2, now()) ON CONFLICT (repo) DO UPDATE "
                "SET last_indexed_sha = EXCLUDED.last_indexed_sha, indexed_at = now()",
                repo, sha,
            )
