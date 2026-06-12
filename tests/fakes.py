from types import SimpleNamespace

from codereview.agent.state import CheckResult, ModelFinding, Snippet


def parse_response(findings: list[ModelFinding] | None = None, input_tokens: int = 1000, output_tokens: int = 200):
    return SimpleNamespace(
        parsed_output=CheckResult(findings=findings or []),
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def invalid_parse_response(input_tokens: int = 500, output_tokens: int = 50):
    return SimpleNamespace(
        parsed_output=None,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class FakeAnthropic:
    """Duck-type of AsyncAnthropic for tests: queue of responses or exceptions."""

    def __init__(self, responses: list) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []
        self.messages = SimpleNamespace(parse=self._parse)

    async def _parse(self, **kwargs):
        self.calls.append(kwargs)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeAnthropicByCategory:
    def __init__(self, by_category: dict[str, list]) -> None:
        self._by_cat = {k: list(v) for k, v in by_category.items()}
        self.calls: list[dict] = []
        self.messages = SimpleNamespace(parse=self._parse)

    async def _parse(self, **kwargs):
        self.calls.append(kwargs)
        for cat, queue in self._by_cat.items():
            if f"rubric — {cat}" in kwargs["system"] and queue:
                item = queue.pop(0)
                if isinstance(item, Exception):
                    raise item
                return item
        raise AssertionError("no queued response for this category")


class FakeVoyage:
    """Duck-type of voyageai.AsyncClient."""

    def __init__(self, dim: int = 4, fail_times: int = 0) -> None:
        self.dim = dim
        self.calls: list[tuple[list[str], str, str]] = []
        self._fail = fail_times

    async def embed(self, texts, model, input_type, **kwargs):
        if self._fail > 0:
            self._fail -= 1
            raise RuntimeError("503 from voyage")
        self.calls.append((list(texts), model, input_type))
        return SimpleNamespace(
            embeddings=[[float(len(t) % 97)] * self.dim for t in texts]
        )


class FakeChunkStore:
    """Fidelity notes: search() returns insertion order (the real store orders by
    vector distance) and count() ignores delete_paths — don't write order-sensitive
    or count-after-delete assertions against this fake."""

    def __init__(self, snippets: list[Snippet] | None = None) -> None:
        self.snippets = snippets or []
        self.upserts: list = []
        self.deleted: list[list[str]] = []
        self.index_state: tuple[str, str] | None = None
        self.search_calls: list[dict] = []

    async def upsert(self, chunks, embeddings, commit_sha):
        self.upserts.append((list(chunks), list(embeddings), commit_sha))

    async def delete_paths(self, paths):
        self.deleted.append(list(paths))

    async def wipe(self):
        self.snippets = []
        self.upserts = []

    async def count(self):
        return sum(len(c) for c, _, _ in self.upserts)

    async def search(self, embedding, source_type, k, exclude_path=None):
        self.search_calls.append(
            {"source_type": source_type, "k": k, "exclude_path": exclude_path}
        )
        return [
            s for s in self.snippets
            if s.source_type == source_type and s.path != exclude_path
        ][:k]

    async def set_index_state(self, repo, sha):
        self.index_state = (repo, sha)
