from codereview.stores import InMemoryReviewStore, ReviewRecord


async def test_record_and_query():
    s = InMemoryReviewStore()
    assert await s.has_completed("acme/widgets", 7, "abc") is False
    await s.record(ReviewRecord(repo="acme/widgets", pr_number=7, head_sha="abc", status="completed", trigger="webhook", model="claude-sonnet-4-6"))
    assert await s.has_completed("acme/widgets", 7, "abc") is True
    assert await s.has_completed("acme/widgets", 7, "other") is False
    await s.record(ReviewRecord(repo="acme/widgets", pr_number=8, head_sha="def", status="failed", trigger="webhook", model="claude-sonnet-4-6"))
    rows = await s.recent(50)
    assert len(rows) == 2 and rows[0]["pr_number"] == 8  # newest first
    assert "created_at" in rows[0]
