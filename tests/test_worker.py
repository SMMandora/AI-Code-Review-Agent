import asyncio
from dataclasses import dataclass

from codereview.worker import ReindexJob, ReviewJob, Worker


@dataclass(frozen=True)
class DummyJob:
    n: int


def test_job_dataclasses():
    j = ReviewJob(pr_number=7, head_sha="abc", force=True, trigger="slash")
    assert (j.pr_number, j.head_sha, j.force, j.trigger) == (7, "abc", True, "slash")
    r = ReindexJob(changed=("a.py",), removed=("b.py",), after_sha="def")
    assert r.changed == ("a.py",)


async def test_processes_jobs_in_order():
    seen: list[int] = []
    done = asyncio.Event()

    async def handler(job: DummyJob) -> None:
        seen.append(job.n)
        if job.n == 2:
            done.set()

    w = Worker(job_timeout=5)
    w.register(DummyJob, handler)
    await w.start()
    assert w.enqueue(DummyJob(1)) is True
    assert w.enqueue(DummyJob(2)) is True
    await asyncio.wait_for(done.wait(), timeout=2)
    await w.stop()
    assert seen == [1, 2]


async def test_handler_error_does_not_kill_consumer():
    seen: list[int] = []
    errors: list[tuple[object, BaseException]] = []
    done = asyncio.Event()

    async def handler(job: DummyJob) -> None:
        if job.n == 1:
            raise RuntimeError("boom")
        seen.append(job.n)
        done.set()

    async def on_error(job: object, exc: BaseException) -> None:
        errors.append((job, exc))

    w = Worker(job_timeout=5)
    w.register(DummyJob, handler)
    w.on_error = on_error
    await w.start()
    w.enqueue(DummyJob(1))
    w.enqueue(DummyJob(2))
    await asyncio.wait_for(done.wait(), timeout=2)
    await w.stop()
    assert seen == [2]
    assert len(errors) == 1 and isinstance(errors[0][1], RuntimeError)


async def test_job_timeout_reported_via_on_error():
    errors: list[BaseException] = []
    hit = asyncio.Event()

    async def handler(job: DummyJob) -> None:
        await asyncio.sleep(10)

    async def on_error(job: object, exc: BaseException) -> None:
        errors.append(exc)
        hit.set()

    w = Worker(job_timeout=0.05)
    w.register(DummyJob, handler)
    w.on_error = on_error
    await w.start()
    w.enqueue(DummyJob(1))
    await asyncio.wait_for(hit.wait(), timeout=2)
    await w.stop()
    # asyncio.timeout() converts its own deadline-cancel into TimeoutError outside
    # the with block (CancelledError is only seen for external cancellation)
    assert isinstance(errors[0], TimeoutError)


async def test_enqueue_returns_false_when_full():
    w = Worker(job_timeout=5, maxsize=1)
    # not started: nothing drains the queue
    assert w.enqueue(DummyJob(1)) is True
    assert w.enqueue(DummyJob(2)) is False


async def test_unregistered_job_type_is_dropped():
    w = Worker(job_timeout=5)
    await w.start()
    w.enqueue(DummyJob(1))  # no handler registered
    await asyncio.wait_for(w._queue.join(), timeout=2)  # consumed, not stuck
    assert w.pending() == 0
    await w.stop()  # must not raise
