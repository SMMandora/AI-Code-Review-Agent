import pytest

from codereview.agent.prompting import render_user
from codereview.agent.state import CATEGORIES, PRMeta
from codereview.diff import parse_diff
from tests.prompt_regression.loader import load_cases

ALL_CASES = load_cases()


def test_at_least_ten_cases_per_check():
    for check in CATEGORIES:
        n = len([c for c in ALL_CASES if c.check == check])
        assert n >= 10, f"{check} has only {n} adversarial cases"


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda c: f"{c.check}:{c.name}")
def test_case_is_well_formed_and_renders_safely(case):
    files = parse_diff(case.diff)
    assert files, f"{case.name}: diff does not parse"
    if case.planted_bug:
        df = {f.path: f for f in files}[case.planted_bug["path"]]
        assert case.planted_bug["line"] in df.commentable
    if case.must_still_find:
        assert case.planted_bug, f"{case.name}: must_still_find without planted_bug"
    pr = PRMeta(1, case.pr_title, case.pr_body, "mallory", "sha", "main", "main")
    rendered = render_user(pr, files, None, case.check)
    # trusted instruction footer must still terminate the prompt (nothing escaped a fence)
    assert rendered.rstrip().endswith("Use NEW-side line numbers that appear in the diffs above.")
