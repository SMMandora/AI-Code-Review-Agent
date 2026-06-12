import logging

from codereview.agent.cost import estimate_tokens
from codereview.agent.state import PRMeta, RetrievedContext
from codereview.diff import DiffFile

log = logging.getLogger(__name__)


class Retriever:
    """Spec §9 retrieval: per-file code chunks + once-per-PR style/pr_comment chunks."""

    def __init__(
        self,
        store,
        embedder,
        per_file_k: int = 4,
        style_k: int = 3,
        comments_k: int = 3,
        max_context_tokens: int = 6000,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.per_file_k = per_file_k
        self.style_k = style_k
        self.comments_k = comments_k
        self.max_context_tokens = max_context_tokens

    async def retrieve(self, pr: PRMeta, files: list[DiffFile]) -> RetrievedContext:
        queries = [f"{f.path}\n{f.added_text[:1500]}" for f in files]
        global_query = pr.title + "\n" + "\n".join(f.path for f in files)
        embeddings = await self.embedder.embed_queries([*queries, global_query])

        ctx = RetrievedContext()
        budget = self.max_context_tokens

        def take(snippets, sink):
            nonlocal budget
            for s in snippets:
                t = estimate_tokens(s.content)
                if budget - t < 0:
                    return
                budget -= t
                sink.append(s)

        global_emb = embeddings[-1]
        take(await self.store.search(global_emb, "style", self.style_k), ctx.global_snippets)
        take(
            await self.store.search(global_emb, "pr_comment", self.comments_k),
            ctx.global_snippets,
        )
        for f, emb in zip(files, embeddings[:-1], strict=True):
            sink: list = []
            take(
                await self.store.search(emb, "code", self.per_file_k, exclude_path=f.path),
                sink,
            )
            ctx.per_file[f.path] = sink
        return ctx
