import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReviewJob:
    pr_number: int
    head_sha: str | None = None
    force: bool = False
    trigger: str = "webhook"


@dataclass(frozen=True)
class ReindexJob:
    changed: tuple[str, ...]
    removed: tuple[str, ...]
    after_sha: str


Handler = Callable[[object], Awaitable[None]]
ErrorHook = Callable[[object, BaseException], Awaitable[None]]


class Worker:
    """Single-consumer in-process job queue (spec §6)."""

    def __init__(self, job_timeout: float = 120.0, maxsize: int = 100) -> None:
        self._queue: asyncio.Queue[object] = asyncio.Queue(maxsize=maxsize)
        self._handlers: dict[type, Handler] = {}
        self._task: asyncio.Task[None] | None = None
        self.job_timeout = job_timeout
        self.on_error: ErrorHook | None = None

    def register(self, job_type: type, handler: Handler) -> None:
        self._handlers[job_type] = handler

    def enqueue(self, job: object) -> bool:
        try:
            self._queue.put_nowait(job)
            return True
        except asyncio.QueueFull:
            log.error("worker queue full, dropping job=%r", job)
            return False

    def pending(self) -> int:
        return self._queue.qsize()

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name="worker-consumer")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run(self) -> None:
        while True:
            job = await self._queue.get()
            try:
                handler = self._handlers.get(type(job))
                if handler is None:
                    log.error("no handler for job type %s, dropping", type(job).__name__)
                    continue
                try:
                    async with asyncio.timeout(self.job_timeout):
                        await handler(job)
                except asyncio.CancelledError:
                    raise
                except BaseException as exc:  # noqa: B036 - report TimeoutError too
                    log.exception("job failed: %r", job)
                    if self.on_error is not None:
                        with contextlib.suppress(Exception):
                            await self.on_error(job, exc)
            finally:
                self._queue.task_done()
