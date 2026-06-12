import tomllib
from pathlib import Path

import yaml

from codereview.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


def test_compose_is_valid_yaml_with_pgvector():
    data = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    assert "pgvector/pgvector:pg16" in data["services"]["db"]["image"]
    assert "app" in data["services"]


def test_fly_toml_parses_and_checks_healthz():
    data = tomllib.loads((ROOT / "fly.toml").read_text())
    assert data["http_service"]["internal_port"] == 8000
    assert data["http_service"]["checks"][0]["path"] == "/healthz"


def test_dockerfile_basics():
    text = (ROOT / "Dockerfile").read_text()
    assert "python:3.12-slim" in text
    assert "USER appuser" in text
    assert "--factory" in text


def test_env_example_covers_all_settings():
    text = (ROOT / ".env.example").read_text()
    declared = {line.split("=")[0] for line in text.splitlines()
                if line and not line.startswith("#") and "=" in line}
    for name in Settings.model_fields:
        assert name.upper() in declared, f"{name.upper()} missing from .env.example"
