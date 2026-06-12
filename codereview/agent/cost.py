from collections.abc import Iterable

# (input, output) USD per million tokens — verified against claude-api reference 2026-06-11
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


def estimate_tokens(text: str) -> int:
    return int(len(text) / 3.5) + 1


def total_cost_usd(model: str, pairs: Iterable[tuple[int, int]]) -> float:
    pin, pout = PRICES_PER_MTOK[model]
    return sum(i * pin + o * pout for i, o in pairs) / 1_000_000


def preflight_estimate_usd(model: str, diff_chars: int) -> float:
    """Worst-case-ish estimate before any model call (spec §10 fetch node).

    Per check node: diff tokens + ~6000 RAG context tokens + ~1500 template tokens
    of input, ~2000 output tokens. Four nodes.
    """
    pin, pout = PRICES_PER_MTOK[model]
    in_tok = diff_chars / 3.5 + 7500
    out_tok = 2000.0
    return 4 * (in_tok * pin + out_tok * pout) / 1_000_000
