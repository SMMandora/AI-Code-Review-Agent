import logging
from contextlib import asynccontextmanager

from anthropic import AsyncAnthropic
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from codereview.agent.graph import make_run_review
from codereview.agent.state import AgentDeps
from codereview.github.client import GitHubClient
from codereview.log import configure_logging
from codereview.settings import Settings
from codereview.stores import InMemoryReviewStore, ReviewRecord
from codereview.web.webhooks import router as webhook_router
from codereview.worker import ReviewJob, Worker

log = logging.getLogger(__name__)


def make_on_error(deps: AgentDeps):
    """Records rows for jobs that die outside run_review (e.g. worker timeout)."""

    async def on_error(job: object, exc: BaseException) -> None:
        if isinstance(job, ReviewJob):
            await deps.reviews.record(
                ReviewRecord(
                    repo=deps.settings.github_repo,
                    pr_number=job.pr_number,
                    head_sha=job.head_sha or "",
                    status="failed",
                    trigger=job.trigger,
                    model=deps.settings.default_model,
                    error=repr(exc)[:500],
                )
            )

    return on_error


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging(settings.log_level)
        app.state.settings = settings
        app.state.worker = Worker()
        app.state.deps = None
        gh = None
        if settings.github_token and settings.anthropic_api_key:
            gh = GitHubClient(settings.github_token, settings.github_repo)
            anthropic_client = AsyncAnthropic(
                api_key=settings.anthropic_api_key, timeout=30.0, max_retries=1
            )
            deps = AgentDeps(
                settings=settings,
                gh=gh,
                anthropic=anthropic_client,
                reviews=InMemoryReviewStore(),  # replaced by PgReviewStore in Task 12
            )
            app.state.deps = deps
            app.state.worker.register(ReviewJob, make_run_review(deps))
            app.state.worker.on_error = make_on_error(deps)
        await app.state.worker.start()
        log.info("started: repo=%s", settings.github_repo)
        yield
        await app.state.worker.stop()
        if gh is not None:
            await gh.aclose()

    app = FastAPI(title="AI Code Review Agent", lifespan=lifespan)
    app.include_router(webhook_router)

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        return JSONResponse({"ok": True, "db": False})

    return app
