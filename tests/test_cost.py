import pytest

from codereview.agent.cost import (
    PRICES_PER_MTOK,
    estimate_tokens,
    preflight_estimate_usd,
    total_cost_usd,
)


def test_price_table_models():
    assert set(PRICES_PER_MTOK) == {"claude-sonnet-4-6", "claude-opus-4-8", "claude-haiku-4-5"}
    assert PRICES_PER_MTOK["claude-sonnet-4-6"] == (3.00, 15.00)


def test_estimate_tokens():
    assert estimate_tokens("x" * 350) == 101  # 350/3.5 + 1


def test_total_cost_unknown_model_raises():
    with pytest.raises(KeyError):
        total_cost_usd("gpt-9", [(1, 1)])


def test_total_cost_usd():
    pairs = [(100_000, 10_000), (50_000, 5_000)]
    assert total_cost_usd("claude-sonnet-4-6", pairs) == pytest.approx(0.675)


def test_preflight_estimate():
    # zero diff chars: 4 * (7500*3 + 2000*15) / 1e6 = 0.21
    assert preflight_estimate_usd("claude-sonnet-4-6", 0) == pytest.approx(0.21)
    assert preflight_estimate_usd("claude-sonnet-4-6", 700_000) > 0.50
