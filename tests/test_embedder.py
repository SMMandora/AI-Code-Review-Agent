import pytest

from codereview.rag.embedder import Embedder
from tests.fakes import FakeVoyage


async def test_batches_of_128():
    fake = FakeVoyage()
    e = Embedder(api_key="k", client=fake)
    out = await e.embed_documents([f"t{i}" for i in range(251)])
    assert len(out) == 251
    assert [len(c[0]) for c in fake.calls] == [128, 123]
    assert all(c[2] == "document" for c in fake.calls)


async def test_query_input_type():
    fake = FakeVoyage()
    e = Embedder(api_key="k", client=fake)
    await e.embed_queries(["q"])
    assert fake.calls[0][2] == "query"


async def test_truncates_to_8000_chars():
    fake = FakeVoyage()
    e = Embedder(api_key="k", client=fake)
    await e.embed_documents(["x" * 20_000])
    assert len(fake.calls[0][0][0]) == 8000


async def test_retries_once_then_succeeds():
    fake = FakeVoyage(fail_times=1)
    e = Embedder(api_key="k", client=fake, retry_wait=0)
    out = await e.embed_documents(["a"])
    assert len(out) == 1


async def test_double_failure_raises():
    fake = FakeVoyage(fail_times=2)
    e = Embedder(api_key="k", client=fake, retry_wait=0)
    with pytest.raises(RuntimeError):
        await e.embed_documents(["a"])
