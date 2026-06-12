import logging
from pathlib import Path

import asyncpg
from pgvector.asyncpg import register_vector

from codereview.stores import ReviewRecord

log = logging.getLogger(__name__)
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Database:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    @classmethod
    async def connect(cls, dsn: str) -> "Database":
        # Schema (incl. CREATE EXTENSION vector) must exist BEFORE register_vector,
        # which looks the type up in pg_type.
        conn = await asyncpg.connect(dsn)
        try:
            await conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
        finally:
            await conn.close()
        pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5, init=register_vector)
        return cls(pool)

    async def close(self) -> None:
        await self.pool.close()

    async def ping(self) -> bool:
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval("SELECT 1") == 1
        except Exception:
            return False


class PgReviewStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def record(self, r: ReviewRecord) -> None:
        async with self._db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO reviews (repo, pr_number, head_sha, status, "trigger", model,
                    findings_total, comments_posted, input_tokens, output_tokens,
                    cost_usd, duration_ms, error, completed_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13, now())
                """,
                r.repo, r.pr_number, r.head_sha, r.status, r.trigger, r.model,
                r.findings_total, r.comments_posted, r.input_tokens, r.output_tokens,
                r.cost_usd, r.duration_ms, r.error,
            )

    async def has_completed(self, repo: str, pr_number: int, head_sha: str) -> bool:
        async with self._db.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM reviews WHERE repo=$1 AND pr_number=$2 "
                "AND head_sha=$3 AND status='completed')",
                repo, pr_number, head_sha,
            )

    async def recent(self, limit: int = 50) -> list[dict]:
        async with self._db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM reviews ORDER BY id DESC LIMIT $1", limit
            )
        return [dict(row) for row in rows]
