from codereview.agent.state import Finding
from evals.matching import Expected, match_findings


def mk(path="a.py", line=3, cat="correctness", msg="off-by-one in slice", sev="medium"):
    return Finding(path=path, line=line, severity=sev, message=msg, category=cat)


EX = Expected(path="a.py", line_start=2, line_end=4, category="correctness", pattern="off.by.one")


def test_match_within_line_range_and_pattern():
    matched, missed, extra = match_findings([mk()], [EX])
    assert len(matched) == 1 and missed == [] and extra == []


def test_pattern_is_case_insensitive_and_checks_suggestion():
    f = mk(msg="bad slice")
    f2 = f.model_copy(update={"suggestion": "start = (page - 1)  # Off-By-One fix"})
    matched, _, _ = match_findings([f2], [EX])
    assert len(matched) == 1


def test_category_must_match():
    matched, missed, _ = match_findings([mk(cat="style")], [EX])
    assert matched == [] and missed == [EX]


def test_line_out_of_range_misses():
    matched, missed, _ = match_findings([mk(line=9)], [EX])
    assert matched == [] and len(missed) == 1


def test_greedy_one_to_one():
    two_expected = [EX, EX]
    matched, missed, extra = match_findings([mk()], two_expected)
    assert len(matched) == 1 and len(missed) == 1 and extra == []


def test_unmatched_produced_reported_as_extra():
    matched, _, extra = match_findings([mk(), mk(path="other.py")], [EX])
    assert len(matched) == 1 and len(extra) == 1
