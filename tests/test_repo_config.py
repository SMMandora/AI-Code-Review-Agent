import pytest
from pydantic import ValidationError

from codereview.repo_config import RepoConfig, load_repo_config


def test_defaults():
    c = RepoConfig()
    assert c.model == "claude-sonnet-4-6"
    assert c.severity_threshold == "low"
    assert c.skip_files == [] and c.custom_rules == [] and c.warnings == []


def test_unknown_model_rejected():
    with pytest.raises(ValidationError):
        RepoConfig(model="gpt-9")


def test_skips_globs():
    c = RepoConfig(skip_files=["**/migrations/**", "*.lock", "dist/**"])
    assert c.skips("app/migrations/0001_init.py")
    assert c.skips("poetry.lock")
    assert c.skips("sub/dir/poetry.lock")
    assert c.skips("dist/bundle.js")
    assert not c.skips("app/models.py")


class FakeGH:
    def __init__(self, yml: str | None) -> None:
        self.yml = yml
        self.calls: list[tuple[str, str]] = []

    async def get_file(self, path: str, ref: str) -> str | None:
        self.calls.append((path, ref))
        return self.yml


async def test_load_valid_yaml():
    gh = FakeGH(
        "skip_files:\n  - '*.lock'\ncustom_rules:\n  - No print statements.\n"
        "model: claude-haiku-4-5\nseverity_threshold: medium\n"
    )
    cfg = await load_repo_config(gh, "main", default_model="claude-sonnet-4-6")
    assert cfg.model == "claude-haiku-4-5"
    assert cfg.severity_threshold == "medium"
    assert cfg.skips("poetry.lock")
    assert cfg.warnings == []
    assert gh.calls == [(".codereview.yml", "main")]


async def test_missing_file_yields_defaults():
    cfg = await load_repo_config(FakeGH(None), "main", default_model="claude-opus-4-8")
    assert cfg.model == "claude-opus-4-8" and cfg.warnings == []


async def test_invalid_yaml_falls_back_with_warning():
    cfg = await load_repo_config(FakeGH("model: [unclosed"), "main", default_model="claude-sonnet-4-6")
    assert cfg.model == "claude-sonnet-4-6"
    assert any("could not be parsed" in w for w in cfg.warnings)


async def test_unknown_model_falls_back_with_warning():
    cfg = await load_repo_config(FakeGH("model: gpt-9\n"), "main", default_model="claude-sonnet-4-6")
    assert cfg.model == "claude-sonnet-4-6"
    assert any("invalid" in w for w in cfg.warnings)


async def test_unknown_keys_warn_but_load():
    cfg = await load_repo_config(
        FakeGH("model: claude-sonnet-4-6\nbanana: true\n"), "main",
        default_model="claude-sonnet-4-6",
    )
    assert any("unknown key" in w for w in cfg.warnings)


async def test_missing_model_key_uses_default():
    cfg = await load_repo_config(
        FakeGH("severity_threshold: high\n"), "main", default_model="claude-haiku-4-5"
    )
    assert cfg.model == "claude-haiku-4-5" and cfg.severity_threshold == "high"
