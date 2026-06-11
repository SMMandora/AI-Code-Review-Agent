import pytest

from codereview.settings import Settings


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
