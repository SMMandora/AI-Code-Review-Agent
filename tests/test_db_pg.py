from codereview.stores import ReviewRecord
from tests.conftest import pg

pytestmark = pg


async def test_schema_applies_and_ping(db):
    assert await db.ping() is True


async def test_pg_review_store_roundtrip(db):
    from codereview.db import PgReviewStore

    store = PgReviewStore(db)
    await store.record(
        ReviewRecord(
            repo="acme/widgets", pr_number=7, head_sha="abc", status="completed",
            trigger="webhook", model="claude-sonnet-4-6", findings_total=3,
            comments_posted=2, input_tokens=1000, output_tokens=200,
            cost_usd=0.0123, duration_ms=4200, error=None,
        )
    )
    assert await store.has_completed("acme/widgets", 7, "abc") is True
    assert await store.has_completed("acme/widgets", 7, "zzz") is False
    [row] = await store.recent(10)
    assert row["pr_number"] == 7 and float(row["cost_usd"]) == 0.0123
    assert row["created_at"] is not None
