from app.discount import apply_percentage


def test_placeholder():
    assert apply_percentage(100, 10) == 90.0
