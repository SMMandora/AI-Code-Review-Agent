import io
import tarfile

from codereview.rag.indexer import Indexer, extract_tarball
from tests.fakes import FakeChunkStore, FakeVoyage


def make_tarball(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for path, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name=f"acme-widgets-abc123/{path}")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class FakeGitHub:
    def __init__(self, files: dict[str, str]) -> None:
        self.files = files

    async def get_file(self, path: str, ref: str) -> str | None:
        return self.files.get(path)


def make_indexer(store=None):
    from codereview.rag.embedder import Embedder

    store = store or FakeChunkStore()
    embedder = Embedder(api_key="k", client=FakeVoyage(dim=1024), retry_wait=0)
    return Indexer(store=store, embedder=embedder), store


def test_extract_tarball_strips_root_and_filters():
    tar = make_tarball({
        "app/a.py": "x = 1",
        "README.md": "docs",
        "big.py": "x" * 250_000,
        "image.png": "bin",
    })
    items = dict(extract_tarball(tar))
    assert set(items) == {"app/a.py", "README.md", "image.png"}  # size filter only here
    assert items["app/a.py"] == "x = 1"


async def test_seed_from_tarball():
    idx, store = make_indexer()
    tar = make_tarball({
        "app/a.py": "\n".join(["x = 1"] * 70),
        "README.md": "Use logging.",
        "image.png": "bin",
    })
    n = await idx.seed_from_tarball(tar, commit_sha="abc123", repo="acme/widgets")
    assert n == 3  # 2 code chunks + 1 style chunk; png produced none
    [(chunks, embeddings, sha)] = store.upserts
    assert sha == "abc123" and len(chunks) == 3 and len(embeddings[0]) == 1024
    assert store.index_state == ("acme/widgets", "abc123")


async def test_index_pr_comments():
    idx, store = make_indexer()
    n = await idx.index_pr_comments(
        [{"path": "app/a.py", "body": "Use the logger."}, {"path": "x", "body": ""}],
        commit_sha="abc123",
    )
    assert n == 1
    [(chunks, _, _)] = store.upserts
    assert chunks[0].source_type == "pr_comment"


async def test_reindex_paths_deletes_then_indexes():
    idx, store = make_indexer()
    gh = FakeGitHub({"app/a.py": "x = 1\ny = 2", "docs/guide.md": "Style."})
    n = await idx.reindex_paths(
        gh,
        changed=["app/a.py", "docs/guide.md", "gone.py"],
        removed=["app/old.py"],
        after_sha="def456",
        repo="acme/widgets",
    )
    assert store.deleted == [["app/a.py", "docs/guide.md", "gone.py", "app/old.py"]]
    assert n == 2  # gone.py fetch returned None
    assert store.index_state == ("acme/widgets", "def456")


async def test_skip_files_respected_when_provided():
    idx, store = make_indexer()
    idx.skip = lambda p: p.endswith(".lock")
    tar = make_tarball({"poetry.lock": "x", "app/a.py": "x = 1"})
    n = await idx.seed_from_tarball(tar, commit_sha="s", repo="r")
    assert n == 1
