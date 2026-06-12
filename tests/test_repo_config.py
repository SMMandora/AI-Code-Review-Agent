import pytest
from pydantic import ValidationError

from codereview.repo_config import RepoConfig


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
