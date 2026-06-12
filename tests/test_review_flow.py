import httpx
import pytest
import respx

from codereview.agent.graph import make_run_review
from codereview.agent.state import AgentDeps, ModelFinding
from codereview.github.client import GitHubClient
from codereview.stores import InMemoryReviewStore
from codereview.worker import ReviewJob
from tests.diff_fixtures import NEW_FILE_DIFF
from tests.fakes import FakeAnthropic, parse_response

BASE = "https://api.github.com"
REPO = "acme/widgets"

PR_JSON = {
    "number": 7,
    "title": "Add util",
    "body": "Adds division helper",
    "user": {"login": "alice"},
    "head": {"sha": "abc123"},
    "base": {"ref": "main", "repo": {"default_branch": "main"}},
}


@pytest.fixture
async def gh():
    client = GitHubClient("test-token", REPO)
    yield client
    await client.aclose()


def mock_github(reviews_json=None):
    respx.get(f"{BASE}/repos/{REPO}/pulls/7", headers={"Accept": "application/vnd.github.diff"}).mock(
        return_value=httpx.Response(200, text=NEW_FILE_DIFF)
    )
    respx.get(f"{BASE}/repos/{REPO}/pulls/7").mock(return_value=httpx.Response(200, json=PR_JSON))
    respx.get(f"{BASE}/repos/{REPO}/pulls/7/reviews").mock(
        return_value=httpx.Response(200, json=reviews_json or [])
    )
    respx.get(f"{BASE}/repos/{REPO}/contents/app/util.py").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    return respx.post(f"{BASE}/repos/{REPO}/pulls/7/reviews").mock(
        return_value=httpx.Response(200, json={"id": 99})
    )


@respx.mock
async def test_full_flow_posts_single_review(settings, gh):
    post_route = mock_github()
    finding = ModelFinding(
        path="app/util.py", line=2, severity="high",
        message="ZeroDivisionError when count is 0",
    )
    store = InMemoryReviewStore()
    deps = AgentDeps(settings=settings, gh=gh, anthropic=FakeAnthropic([parse_response([finding])]), reviews=store)
    await make_run_review(deps)(ReviewJob(pr_number=7, head_sha="abc123"))

    assert post_route.call_count == 1
    import json

    sent = json.loads(post_route.calls.last.request.content)
    assert sent["commit_id"] == "abc123"
    assert "<!-- ai-code-review:v1 sha=abc123 -->" in sent["body"]
    assert len(sent["comments"]) == 1
    c = sent["comments"][0]
    assert c["path"] == "app/util.py" and c["line"] == 2 and c["side"] == "RIGHT"
    assert "ZeroDivision" in c["body"]

    [row] = [r for r, _ in store.rows]
    assert row.status == "completed" and row.cost_usd > 0 and row.input_tokens == 1000


@respx.mock
async def test_second_run_is_idempotent(settings, gh):
    post_route = mock_github()
    finding = ModelFinding(path="app/util.py", line=2, severity="high", message="bug")
    store = InMemoryReviewStore()
    deps = AgentDeps(settings=settings, gh=gh, anthropic=FakeAnthropic([parse_response([finding])]), reviews=store)
    run = make_run_review(deps)
    await run(ReviewJob(pr_number=7, head_sha="abc123"))
    await run(ReviewJob(pr_number=7, head_sha="abc123"))
    assert post_route.call_count == 1
    statuses = [r.status for r, _ in store.rows]
    assert statuses == ["completed", "skipped"]


@respx.mock
async def test_marker_in_existing_github_review_skips(settings, gh):
    post_route = mock_github(
        reviews_json=[{"body": "old review\n<!-- ai-code-review:v1 sha=abc123 -->"}]
    )
    store = InMemoryReviewStore()
    deps = AgentDeps(settings=settings, gh=gh, anthropic=FakeAnthropic([]), reviews=store)
    await make_run_review(deps)(ReviewJob(pr_number=7, head_sha="abc123"))
    assert post_route.call_count == 0
    assert store.rows[0][0].status == "skipped"


@respx.mock
async def test_force_bypasses_idempotency(settings, gh):
    post_route = mock_github(
        reviews_json=[{"body": "old review\n<!-- ai-code-review:v1 sha=abc123 -->"}]
    )
    finding = ModelFinding(path="app/util.py", line=2, severity="high", message="bug")
    store = InMemoryReviewStore()
    deps = AgentDeps(settings=settings, gh=gh, anthropic=FakeAnthropic([parse_response([finding])]), reviews=store)
    await make_run_review(deps)(ReviewJob(pr_number=7, head_sha="abc123", force=True, trigger="slash"))
    assert post_route.call_count == 1


@respx.mock
async def test_pipeline_crash_records_failed_row(settings):
    # gh client pointing at a base URL with no mocked routes -> fetch raises
    gh = GitHubClient("test-token", REPO)
    respx.get(f"{BASE}/repos/{REPO}/pulls/7").mock(return_value=httpx.Response(500, text="boom"))
    store = InMemoryReviewStore()
    deps = AgentDeps(settings=settings, gh=gh, anthropic=FakeAnthropic([]), reviews=store)
    await make_run_review(deps)(ReviewJob(pr_number=7, head_sha="abc123"))
    await gh.aclose()
    assert store.rows[0][0].status == "failed"
    assert store.rows[0][0].error
