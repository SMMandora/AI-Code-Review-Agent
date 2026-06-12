def apply_percentage(price: float, pct: float) -> float:
    """Apply a percentage discount (0-100)."""
    return price * (1 - pct / 100)


def apply_flat(price: float, amount: float) -> float:
    """Apply a flat discount, floored at zero."""
    result = price - amount
    return max(result, 0.0)
