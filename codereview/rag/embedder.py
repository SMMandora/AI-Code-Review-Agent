import asyncio
import logging

import voyageai

log = logging.getLogger(__name__)

EMBED_MODEL = "voyage-code-3"  # 1024-dim, matches schema.sql vector(1024)
MAX_CHARS = 8000


class Embedder:
    def __init__(
        self,
        api_key: str,
        model: str = EMBED_MODEL,
        batch_size: int = 128,
        retry_wait: float = 2.0,
        client=None,
    ) -> None:
        self.model = model
        self.batch_size = batch_size
        self.retry_wait = retry_wait
        self._client = client or voyageai.AsyncClient(api_key=api_key)

    async def _embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = [t[:MAX_CHARS] for t in texts[i : i + self.batch_size]]
            for attempt in (1, 2):
                try:
                    result = await self._client.embed(
                        batch, model=self.model, input_type=input_type
                    )
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    log.warning("voyage embed failed, retrying once")
                    await asyncio.sleep(self.retry_wait)
            out.extend(result.embeddings)
        return out

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts, "document")

    async def embed_queries(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts, "query")
