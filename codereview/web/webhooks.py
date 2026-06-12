import json
import logging

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from codereview.settings import Settings
from codereview.web.security import verify_signature
from codereview.worker import ReindexJob, ReviewJob, Worker

log = logging.getLogger(__name__)
router = APIRouter()

PR_ACTIONS = {"opened", "synchronize", "reopened"}


def route_event(
    event: str, payload: dict, settings: Settings, worker: Worker
) -> tuple[int, dict | None]:
    """Pure routing: returns (status_code, body). 202=queued, 200=pong, 204=ignored, 503=full."""
    if event == "ping":
        return 200, {"ok": True}

    repo = (payload.get("repository") or {}).get("full_name", "")
    if repo != settings.github_repo:
        return 204, None

    if event == "pull_request" and payload.get("action") in PR_ACTIONS:
        job = ReviewJob(
            pr_number=payload["number"],
            head_sha=payload["pull_request"]["head"]["sha"],
        )
        return (202, {"queued": True}) if worker.enqueue(job) else (503, {"queued": False})

    if event == "issue_comment" and payload.get("action") == "created":
        issue = payload.get("issue") or {}
        comment = payload.get("comment") or {}
        body = (comment.get("body") or "").strip()
        allowed = comment.get("author_association") in {"OWNER", "MEMBER", "COLLABORATOR"}
        if "pull_request" in issue and body.startswith("/review again") and allowed:
            job = ReviewJob(pr_number=issue["number"], force=True, trigger="slash")
            return (202, {"queued": True}) if worker.enqueue(job) else (503, {"queued": False})
        return 204, None

    if event == "push":
        default = payload["repository"].get("default_branch", "main")
        if payload.get("ref") != f"refs/heads/{default}":
            return 204, None
        file_state: dict[str, str] = {}  # path -> "changed" | "removed"
        for c in payload.get("commits", []):
            for path in [*c.get("added", []), *c.get("modified", [])]:
                file_state[path] = "changed"
            for path in c.get("removed", []):
                file_state[path] = "removed"
        job = ReindexJob(
            changed=tuple(sorted(p for p, s in file_state.items() if s == "changed")),
            removed=tuple(sorted(p for p, s in file_state.items() if s == "removed")),
            after_sha=payload.get("after", ""),
        )
        return (202, {"queued": True}) if worker.enqueue(job) else (503, {"queued": False})

    return 204, None


@router.post("/webhooks/github")
async def github_webhook(request: Request) -> Response:
    body = await request.body()
    settings: Settings = request.app.state.settings
    sig = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(settings.github_webhook_secret, body, sig):
        return JSONResponse({"error": "invalid signature"}, status_code=401)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    event = request.headers.get("X-GitHub-Event", "")
    status, resp_body = route_event(event, payload, settings, request.app.state.worker)
    if resp_body is None:
        return Response(status_code=status)
    return JSONResponse(resp_body, status_code=status)
