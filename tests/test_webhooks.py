import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from codereview.web.app import create_app
from codereview.web.webhooks import route_event
from codereview.worker import ReindexJob, ReviewJob, Worker


@pytest.fixture
def app_settings(settings):
    # No anthropic key -> lifespan registers no review handler, so an enqueued job
    # can never trigger a background GitHubClient call against the real API.
    return settings.model_copy(update={"anthropic_api_key": ""})


def sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def make_pr_payload(repo: str = "acme/widgets", action: str = "opened") -> dict:
    return {
        "action": action,
        "number": 7,
        "repository": {"full_name": repo, "default_branch": "main"},
        "pull_request": {"number": 7, "head": {"sha": "abc123"}},
    }


def post_event(client: TestClient, secret: str, event: str, payload: dict, sig: str | None = "auto"):
    body = json.dumps(payload).encode()
    headers = {"X-GitHub-Event": event, "Content-Type": "application/json"}
    if sig == "auto":
        headers["X-Hub-Signature-256"] = sign(secret, body)
    elif sig is not None:
        headers["X-Hub-Signature-256"] = sig
    return client.post("/webhooks/github", content=body, headers=headers)


def test_invalid_signature_rejected(app_settings):
    app = create_app(app_settings)
    with TestClient(app) as client:
        r = post_event(client, "wrong", "pull_request", make_pr_payload())
        assert r.status_code == 401


def test_missing_signature_rejected(app_settings):
    app = create_app(app_settings)
    with TestClient(app) as client:
        r = post_event(client, app_settings.github_webhook_secret, "ping", {}, sig=None)
        assert r.status_code == 401


def test_ping_returns_200(app_settings):
    app = create_app(app_settings)
    with TestClient(app) as client:
        r = post_event(client, app_settings.github_webhook_secret, "ping", {"zen": "x"})
        assert r.status_code == 200


def test_pr_opened_accepted(app_settings):
    # queue semantics covered by route_event unit tests; consumption is async
    app = create_app(app_settings)
    with TestClient(app) as client:
        r = post_event(client, app_settings.github_webhook_secret, "pull_request", make_pr_payload())
        assert r.status_code == 202


def test_pr_irrelevant_action_ignored(app_settings):
    app = create_app(app_settings)
    with TestClient(app) as client:
        payload = make_pr_payload(action="labeled")
        r = post_event(client, app_settings.github_webhook_secret, "pull_request", payload)
        assert r.status_code == 204
        assert app.state.worker.pending() == 0


def test_wrong_repo_ignored(app_settings):
    app = create_app(app_settings)
    with TestClient(app) as client:
        payload = make_pr_payload(repo="other/repo")
        r = post_event(client, app_settings.github_webhook_secret, "pull_request", payload)
        assert r.status_code == 204


def test_unknown_event_ignored(app_settings):
    app = create_app(app_settings)
    with TestClient(app) as client:
        r = post_event(client, app_settings.github_webhook_secret, "watch", {"repository": {"full_name": "acme/widgets"}})
        assert r.status_code == 204


def test_healthz(app_settings):
    app = create_app(app_settings)
    with TestClient(app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json()["ok"] is True


# --- route_event unit tests (no HTTP) ---


def test_route_push_to_default_branch_enqueues_reindex(settings):
    w = Worker()
    payload = {
        "ref": "refs/heads/main",
        "after": "deadbeef",
        "repository": {"full_name": "acme/widgets", "default_branch": "main"},
        "commits": [
            {"added": ["a.py"], "modified": ["b.py"], "removed": ["c.py"]},
            {"added": [], "modified": ["a.py"], "removed": []},
        ],
    }
    status, _ = route_event("push", payload, settings, w)
    assert status == 202
    assert w.pending() == 1
    job = w._queue.get_nowait()
    assert isinstance(job, ReindexJob)
    assert sorted(job.changed) == ["a.py", "b.py"]
    assert job.removed == ("c.py",)
    assert job.after_sha == "deadbeef"


def test_route_push_to_feature_branch_ignored(settings):
    w = Worker()
    payload = {
        "ref": "refs/heads/feature",
        "after": "deadbeef",
        "repository": {"full_name": "acme/widgets", "default_branch": "main"},
        "commits": [],
    }
    status, _ = route_event("push", payload, settings, w)
    assert status == 204
    assert w.pending() == 0


def test_route_pr_synchronize_enqueues(settings):
    w = Worker()
    status, _ = route_event("pull_request", make_pr_payload(action="synchronize"), settings, w)
    assert status == 202
    job = w._queue.get_nowait()
    assert isinstance(job, ReviewJob)
    assert job.pr_number == 7 and job.head_sha == "abc123" and job.force is False


def test_route_queue_full_returns_503(settings):
    w = Worker(maxsize=1)
    w.enqueue(object())
    status, _ = route_event("pull_request", make_pr_payload(), settings, w)
    assert status == 503


def test_route_push_modified_then_removed_is_removed(settings):
    w = Worker()
    payload = {
        "ref": "refs/heads/main",
        "after": "deadbeef",
        "repository": {"full_name": "acme/widgets", "default_branch": "main"},
        "commits": [
            {"added": [], "modified": ["gone.py"], "removed": []},
            {"added": [], "modified": [], "removed": ["gone.py"]},
        ],
    }
    route_event("push", payload, settings, w)
    job = w._queue.get_nowait()
    assert "gone.py" not in job.changed
    assert job.removed == ("gone.py",)


def test_route_push_removed_then_readded_is_changed(settings):
    w = Worker()
    payload = {
        "ref": "refs/heads/main",
        "after": "deadbeef",
        "repository": {"full_name": "acme/widgets", "default_branch": "main"},
        "commits": [
            {"added": [], "modified": [], "removed": ["back.py"]},
            {"added": ["back.py"], "modified": [], "removed": []},
        ],
    }
    route_event("push", payload, settings, w)
    job = w._queue.get_nowait()
    assert job.changed == ("back.py",)
    assert "back.py" not in job.removed


def make_comment_payload(
    body="/review again", association="OWNER", is_pr=True, repo="acme/widgets"
):
    issue = {"number": 7}
    if is_pr:
        issue["pull_request"] = {"url": "https://api.github.com/..."}
    return {
        "action": "created",
        "repository": {"full_name": repo, "default_branch": "main"},
        "issue": issue,
        "comment": {"body": body, "author_association": association},
    }


def test_review_again_enqueues_forced_job(settings):
    w = Worker()
    status, _ = route_event("issue_comment", make_comment_payload(), settings, w)
    assert status == 202
    job = w._queue.get_nowait()
    assert isinstance(job, ReviewJob)
    assert job.force is True and job.trigger == "slash"
    assert job.pr_number == 7 and job.head_sha is None  # resolved at fetch time


def test_review_again_with_trailing_text(settings):
    w = Worker()
    payload = make_comment_payload(body="/review again please")
    status, _ = route_event("issue_comment", payload, settings, w)
    assert status == 202


def test_other_comments_ignored(settings):
    w = Worker()
    status, _ = route_event("issue_comment", make_comment_payload(body="nice work"), settings, w)
    assert status == 204 and w.pending() == 0


def test_non_collaborator_cannot_trigger(settings):
    w = Worker()
    payload = make_comment_payload(association="NONE")
    status, _ = route_event("issue_comment", payload, settings, w)
    assert status == 204 and w.pending() == 0


def test_comment_on_plain_issue_ignored(settings):
    w = Worker()
    payload = make_comment_payload(is_pr=False)
    status, _ = route_event("issue_comment", payload, settings, w)
    assert status == 204 and w.pending() == 0
