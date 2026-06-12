"""One-time repository indexing (spec §9). Usage: python scripts/seed_index.py (needs .env)."""

import asyncio
import sys

from codereview.db import Database
from codereview.github.client import GitHubClient
from codereview.rag.embedder import Embedder
from codereview.rag.indexer import Indexer
from codereview.rag.store import ChunkStore
from codereview.settings import Settings


async def main() -> int:
    s = Settings()
    missing = [k for k in ("github_token", "github_repo", "voyage_api_key", "database_url")
               if not getattr(s, k)]
    if missing:
        print(f"FAIL: missing settings: {missing}")
        return 1
    db = await Database.connect(s.database_url)
    gh = GitHubClient(s.github_token, s.github_repo)
    try:
        indexer = Indexer(store=ChunkStore(db), embedder=Embedder(api_key=s.voyage_api_key))
        branch = await gh.get_default_branch()
        print(f"downloading tarball of {s.github_repo}@{branch} ...")
        tar = await gh.get_tarball(branch)
        from codereview.agent.cost import estimate_tokens
        from codereview.rag.indexer import chunk_file, extract_tarball

        est = sum(
            estimate_tokens(c.content)
            for path, text in extract_tarball(tar)
            for c in chunk_file(path, text)
        )
        print(f"~{est:,} tokens to embed (voyage-code-3)")
        n_code = await indexer.seed_from_tarball(tar, commit_sha=branch, repo=s.github_repo)
        comments = await gh.list_recent_review_comments(limit=200)
        n_comments = await indexer.index_pr_comments(comments, commit_sha=branch)
        print(f"OK: indexed {n_code} code/style chunks and {n_comments} PR comments")
        return 0
    finally:
        await gh.aclose()
        await db.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
