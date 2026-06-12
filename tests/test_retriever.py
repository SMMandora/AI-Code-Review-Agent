from codereview.agent.nodes.context import make_context_node
from codereview.agent.state import AgentDeps, PRMeta, RetrievedContext, Snippet
from codereview.diff import parse_diff
from codereview.rag.embedder import Embedder
from codereview.rag.retriever import Retriever
from tests.diff_fixtures import NEW_FILE_DIFF
from tests.fakes import FakeChunkStore, FakeVoyage

PR = PRMeta(7, "Add util", "", "alice", "abc123", "main", "main")


def make_retriever(snippets=None, **kwargs):
    store = FakeChunkStore(snippets or [])
    embedder = Embedder(api_key="k", client=FakeVoyage(dim=1024), retry_wait=0)
    return Retriever(store=store, embedder=embedder, **kwargs), store


async def test_retrieves_per_file_and_global():
    snippets = [
        Snippet("code", "app/math.py", 1, 60, "def x(): pass"),
        Snippet("style", "README.md", 1, 10, "Use logging."),
        Snippet("pr_comment", "app/a.py", 0, 0, "app/a.py: prefer pathlib"),
    ]
    r, store = make_retriever(snippets)
    files = parse_diff(NEW_FILE_DIFF)
    ctx = await r.retrieve(PR, files)
    assert [s.path for s in ctx.per_file["app/util.py"]] == ["app/math.py"]
    assert {s.source_type for s in ctx.global_snippets} == {"style", "pr_comment"}
    code_call = [c for c in store.search_calls if c["source_type"] == "code"][0]
    assert code_call["exclude_path"] == "app/util.py" and code_call["k"] == 4


async def test_token_budget_caps_context():
    big = "x" * 40_000  # ~11.4k tokens each
    snippets = [
        Snippet("style", "README.md", 1, 10, big),
        Snippet("pr_comment", "a", 0, 0, big),
        Snippet("code", "app/math.py", 1, 60, big),
    ]
    r, _ = make_retriever(snippets, max_context_tokens=12_000)
    ctx = await r.retrieve(PR, parse_diff(NEW_FILE_DIFF))
    total = len(ctx.global_snippets) + sum(len(v) for v in ctx.per_file.values())
    assert total == 1  # only the first snippet fits


async def test_empty_store_gives_empty_context():
    r, _ = make_retriever([])
    ctx = await r.retrieve(PR, parse_diff(NEW_FILE_DIFF))
    assert ctx.global_snippets == [] and ctx.per_file == {"app/util.py": []}


async def test_context_node_swallows_retriever_errors(settings):
    class Boom:
        async def retrieve(self, pr, files):
            raise RuntimeError("voyage down")

    deps = AgentDeps(settings=settings, gh=None, anthropic=None, reviews=None, retriever=Boom())
    node = make_context_node(deps)
    out = await node({"pr": PR, "diff_files": parse_diff(NEW_FILE_DIFF)})
    assert isinstance(out["context"], RetrievedContext)
    assert out["context"].global_snippets == []


async def test_context_node_without_retriever(settings):
    deps = AgentDeps(settings=settings, gh=None, anthropic=None, reviews=None)
    node = make_context_node(deps)
    out = await node({"pr": PR, "diff_files": parse_diff(NEW_FILE_DIFF)})
    assert isinstance(out["context"], RetrievedContext)
