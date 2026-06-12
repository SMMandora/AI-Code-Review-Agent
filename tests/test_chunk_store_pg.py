from codereview.rag.indexer import Chunk
from codereview.rag.store import ChunkStore
from tests.conftest import pg

pytestmark = pg


def emb(seed: float) -> list[float]:
    return [seed] + [0.0] * 1023


async def test_upsert_search_delete(db):
    store = ChunkStore(db)
    chunks = [
        Chunk("code", "app/a.py", 1, 60, "def a(): pass"),
        Chunk("code", "app/b.py", 1, 60, "def b(): pass"),
        Chunk("style", "README.md", 1, 10, "Use logging."),
    ]
    await store.upsert(chunks, [emb(1.0), emb(0.9), emb(0.5)], "sha1")
    assert await store.count() == 3

    hits = await store.search(emb(1.0), "code", k=5)
    assert [h.path for h in hits] == ["app/a.py", "app/b.py"]

    hits = await store.search(emb(1.0), "code", k=5, exclude_path="app/a.py")
    assert [h.path for h in hits] == ["app/b.py"]

    hits = await store.search(emb(0.5), "style", k=5)
    assert hits[0].content == "Use logging."

    await store.delete_paths(["app/a.py", "README.md"])
    assert await store.count() == 1

    await store.set_index_state("acme/widgets", "sha2")
    await store.set_index_state("acme/widgets", "sha3")  # upsert path
