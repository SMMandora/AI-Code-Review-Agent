from codereview.settings import Settings


def test_defaults():
    s = Settings(_env_file=None)
    assert s.cost_ceiling_usd == 0.50
    assert s.default_model == "claude-sonnet-4-6"
    assert s.port == 8000
    assert s.github_repo == ""


def test_env_override(monkeypatch):
    monkeypatch.setenv("GITHUB_REPO", "acme/widgets")
    monkeypatch.setenv("COST_CEILING_USD", "0.25")
    s = Settings(_env_file=None)
    assert s.github_repo == "acme/widgets"
    assert s.cost_ceiling_usd == 0.25
