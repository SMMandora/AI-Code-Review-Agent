import os

import pytest
import pytest_asyncio

from codereview.settings import Settings

pg = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="needs Postgres (set DATABASE_URL)"
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        github_token="test-token",
        github_webhook_secret="test-secret",
        github_repo="acme/widgets",
        anthropic_api_key="test-anthropic",
        voyage_api_key="test-voyage",
        database_url="",
    )


@pytest_asyncio.fixture
async def db():
    from codereview.db import Database

    database = await Database.connect(os.environ["DATABASE_URL"])
    async with database.pool.acquire() as conn:
        await conn.execute("TRUNCATE chunks, reviews, index_state")
    yield database
    await database.close()
