import pytest

from evals.loader import load_all

FIXTURES = load_all()


def test_twenty_fixtures():
    assert len(FIXTURES) == 20
    assert [f.name for f in FIXTURES] == [f"pr_{i:03d}" for i in range(1, 21)]


def test_language_mix():
    py = sum(1 for f in FIXTURES if any(d.path.endswith(".py") for d in f.diff_files))
    ts = sum(1 for f in FIXTURES if any(d.path.endswith(".ts") for d in f.diff_files))
    assert py >= 9 and ts >= 9


def test_at_least_three_clean_fixtures():
    assert sum(1 for f in FIXTURES if not f.expected) >= 3


@pytest.mark.parametrize("fx", FIXTURES, ids=lambda f: f.name)
def test_expected_anchors_exist_in_diff(fx):
    by_path = {d.path: d for d in fx.diff_files}
    for ex in fx.expected:
        assert ex.path in by_path, f"{fx.name}: expected path {ex.path} not in diff"
        df = by_path[ex.path]
        window = set(range(ex.line_start, ex.line_end + 1))
        assert window & df.commentable, f"{fx.name}: lines {ex.line_start}-{ex.line_end} not in diff"


@pytest.mark.parametrize("fx", FIXTURES, ids=lambda f: f.name)
def test_categories_valid(fx):
    from codereview.agent.state import CATEGORIES

    for ex in fx.expected:
        assert ex.category in CATEGORIES


@pytest.mark.parametrize("fx", FIXTURES, ids=lambda f: f.name)
def test_same_category_expecteds_cannot_dedup_merge(fx):
    """Two same-category expecteds within dedup's LINE_WINDOW would be merged by
    the production pipeline, making the second expected unmatchable forever."""
    from codereview.agent.dedup import LINE_WINDOW

    by_key: dict = {}
    for ex in fx.expected:
        by_key.setdefault((ex.path, ex.category), []).append(ex)
    for group in by_key.values():
        group.sort(key=lambda e: e.line_start)
        for a, b in zip(group, group[1:], strict=False):
            assert b.line_start - a.line_end > LINE_WINDOW, (
                f"{fx.name}: same-category expecteds {a} and {b} are within the dedup window"
            )
