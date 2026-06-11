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

    if event == "push":
        default = payload["repository"].get("default_branch", "main")
        if payload.get("ref") != f"refs/heads/{default}":
            return 204, None
        changed: set[str] = set()
        removed: set[str] = set()
        for c in payload.get("commits", []):
            changed.update(c.get("added", []))
            changed.update(c.get("modified", []))
            removed.update(c.get("removed", []))
        removed -= changed  # re-added in a later commit wins
        job = ReindexJob(
            changed=tuple(sorted(changed)),
            removed=tuple(sorted(removed)),
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
