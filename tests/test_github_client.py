import base64
import json

import httpx
import pytest
import respx

from codereview.github.client import GitHubClient, GitHubError

BASE = "https://api.github.com"
REPO = "acme/widgets"


@pytest.fixture
async def gh(settings):
    client = GitHubClient(settings.github_token, settings.github_repo)
    yield client
    await client.aclose()


@respx.mock
async def test_get_pr_sends_auth(gh):
    route = respx.get(f"{BASE}/repos/{REPO}/pulls/7").mock(
        return_value=httpx.Response(200, json={"number": 7, "title": "t"})
    )
    pr = await gh.get_pr(7)
    assert pr["number"] == 7
    assert route.calls.last.request.headers["Authorization"] == "Bearer test-token"
    assert "ai-code-review-agent" in route.calls.last.request.headers["User-Agent"]


@respx.mock
async def test_get_pr_diff_uses_diff_accept_header(gh):
    route = respx.get(f"{BASE}/repos/{REPO}/pulls/7").mock(
        return_value=httpx.Response(200, text="diff --git a/x b/x\n")
    )
    diff = await gh.get_pr_diff(7)
    assert diff.startswith("diff --git")
    assert route.calls.last.request.headers["Accept"] == "application/vnd.github.diff"


@respx.mock
async def test_get_file_decodes_base64(gh):
    content = base64.b64encode(b"print('hi')\n").decode()
    respx.get(f"{BASE}/repos/{REPO}/contents/app/x.py").mock(
        return_value=httpx.Response(200, json={"content": content, "encoding": "base64"})
    )
    text = await gh.get_file("app/x.py", "abc123")
    assert text == "print('hi')\n"


@respx.mock
async def test_get_file_404_returns_none(gh):
    respx.get(f"{BASE}/repos/{REPO}/contents/missing.py").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    assert await gh.get_file("missing.py", "abc123") is None


@respx.mock
async def test_create_review_payload(gh):
    route = respx.post(f"{BASE}/repos/{REPO}/pulls/7/reviews").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    comments = [{"path": "a.py", "line": 3, "side": "RIGHT", "body": "issue"}]
    await gh.create_review(7, "abc123", "summary", comments)
    sent = json.loads(route.calls.last.request.content)
    assert sent == {
        "commit_id": "abc123",
        "body": "summary",
        "event": "COMMENT",
        "comments": comments,
    }


@respx.mock
async def test_rate_limit_retries_once(gh):
    route = respx.get(f"{BASE}/repos/{REPO}/pulls/7").mock(
        side_effect=[
            httpx.Response(403, headers={"x-ratelimit-remaining": "0", "retry-after": "0"}),
            httpx.Response(200, json={"number": 7}),
        ]
    )
    pr = await gh.get_pr(7)
    assert pr["number"] == 7
    assert route.call_count == 2


@respx.mock
async def test_error_raises_with_status(gh):
    respx.get(f"{BASE}/repos/{REPO}/pulls/9").mock(return_value=httpx.Response(500, text="boom"))
    with pytest.raises(GitHubError) as exc:
        await gh.get_pr(9)
    assert exc.value.status == 500


@respx.mock
async def test_list_reviews_and_resolve_head(gh):
    respx.get(f"{BASE}/repos/{REPO}/pulls/7/reviews").mock(
        return_value=httpx.Response(200, json=[{"body": "lgtm"}])
    )
    respx.get(f"{BASE}/repos/{REPO}/pulls/7").mock(
        return_value=httpx.Response(200, json={"number": 7, "head": {"sha": "abc123"}})
    )
    assert (await gh.list_reviews(7))[0]["body"] == "lgtm"
    assert await gh.resolve_pr_head(7) == "abc123"
