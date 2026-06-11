import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from codereview.log import configure_logging
from codereview.settings import Settings
from codereview.web.webhooks import router as webhook_router
from codereview.worker import Worker

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging(settings.log_level)
        app.state.settings = settings
        app.state.worker = Worker()
        log.info("started: repo=%s", settings.github_repo)
        yield
        await app.state.worker.stop()

    app = FastAPI(title="AI Code Review Agent", lifespan=lifespan)
    app.include_router(webhook_router)

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        return JSONResponse({"ok": True, "db": False})

    return app
