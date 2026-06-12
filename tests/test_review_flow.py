import httpx
import pytest
import respx

from codereview.agent.graph import make_run_review
from codereview.agent.state import AgentDeps, ModelFinding
from codereview.github.client import GitHubClient
from codereview.stores import InMemoryReviewStore
from codereview.worker import ReviewJob
from tests.diff_fixtures import NEW_FILE_DIFF
from tests.fakes import FakeAnthropic, FakeAnthropicByCategory, parse_response

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


def four_check_responses():
    """One queued response per category, consumed in graph fan-out order."""
    return [
        parse_response([ModelFinding(path="app/util.py", line=2, severity="high",
                                     message="ZeroDivisionError when count is 0")]),
        parse_response([ModelFinding(path="app/util.py", line=3, severity="high",
                                     message="ZeroDivisionError when count is 0")]),  # near-dup
        parse_response([ModelFinding(path="app/util.py", line=4, severity="low",
                                     message="is_even lacks tests")]),
        parse_response([]),
    ]


@respx.mock
async def test_full_flow_four_checks_dedups_and_posts_once(settings, gh):
    post_route = mock_github()
    store = InMemoryReviewStore()
    deps = AgentDeps(settings=settings, gh=gh,
                     anthropic=FakeAnthropic(four_check_responses()), reviews=store)
    await make_run_review(deps)(ReviewJob(pr_number=7, head_sha="abc123"))

    assert post_route.call_count == 1
    import json

    sent = json.loads(post_route.calls.last.request.content)
    assert "<!-- ai-code-review:v1 sha=abc123 -->" in sent["body"]
    assert 1 <= len(sent["comments"]) <= 7
    # the two near-duplicate ZeroDivision findings collapsed to one comment
    zero_div = [c for c in sent["comments"] if "ZeroDivision" in c["body"]]
    assert len(zero_div) == 1
    [row] = [r for r, _ in store.rows]
    assert row.status == "completed"
    assert row.input_tokens == 4000  # 4 nodes x 1000 fake input tokens


@respx.mock
async def test_partial_check_failure_still_posts(settings, gh):
    post_route = mock_github()
    # per-category fake: deterministic regardless of parallel scheduling order
    fake = FakeAnthropicByCategory({
        "correctness": [parse_response([ModelFinding(
            path="app/util.py", line=2, severity="high",
            message="ZeroDivisionError when count is 0")])],
        "security": [RuntimeError("api down"), RuntimeError("api down")],  # both attempts fail
        "style": [parse_response([])],
        "test_coverage": [parse_response([])],
    })
    store = InMemoryReviewStore()
    deps = AgentDeps(settings=settings, gh=gh, anthropic=fake, reviews=store)
    await make_run_review(deps)(ReviewJob(pr_number=7, head_sha="abc123"))
    assert post_route.call_count == 1
    import json

    sent = json.loads(post_route.calls.last.request.content)
    assert "Checks that failed to run" in sent["body"] and "security" in sent["body"]


@respx.mock
async def test_cost_ceiling_blocks_posting(settings, gh):
    post_route = mock_github()
    huge = [parse_response([], input_tokens=80_000, output_tokens=20_000) for _ in range(4)]
    # 4 x (80k*3 + 20k*15)/1e6 = 4 x 0.54 = $2.16 > $0.50
    store = InMemoryReviewStore()
    deps = AgentDeps(settings=settings, gh=gh, anthropic=FakeAnthropic(huge), reviews=store)
    await make_run_review(deps)(ReviewJob(pr_number=7, head_sha="abc123"))
    assert post_route.call_count == 0
    assert store.rows[0][0].status == "cost_exceeded"


@respx.mock
async def test_second_run_is_idempotent(settings, gh):
    post_route = mock_github()
    finding = ModelFinding(path="app/util.py", line=2, severity="high", message="bug")
    store = InMemoryReviewStore()
    deps = AgentDeps(
        settings=settings, gh=gh,
        anthropic=FakeAnthropic([parse_response([finding])] + [parse_response([])] * 3),
        reviews=store,
    )
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
    deps = AgentDeps(
        settings=settings, gh=gh,
        anthropic=FakeAnthropic([parse_response([finding])] + [parse_response([])] * 3),
        reviews=store,
    )
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
