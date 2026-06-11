from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    github_token: str = ""
    github_webhook_secret: str = ""
    github_repo: str = ""  # "owner/name"
    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    database_url: str = ""
    cost_ceiling_usd: float = 0.50
    default_model: str = "claude-sonnet-4-6"
    log_level: str = "INFO"
    port: int = 8000
