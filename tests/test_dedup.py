from codereview.agent.dedup import apply_dedup
from codereview.agent.state import Finding
from codereview.diff import parse_diff
from tests.diff_fixtures import LONG_FILE_DIFF, NEW_FILE_DIFF


def mk(path="app/util.py", line=2, sev="medium", cat="correctness", msg="division by zero risk"):
    return Finding(path=path, line=line, severity=sev, message=msg, category=cat)


def files():
    return parse_diff(NEW_FILE_DIFF)


def test_severity_threshold_filters():
    out = apply_dedup([mk(sev="low"), mk(line=3, sev="high")], files(), threshold="medium")
    assert [f.severity for f in out.inline] == ["high"]


def test_near_duplicates_keep_highest_severity():
    a = mk(line=2, sev="medium", cat="correctness", msg="possible ZeroDivisionError here")
    b = mk(line=3, sev="high", cat="security", msg="possible ZeroDivisionError here")
    out = apply_dedup([a, b], files(), threshold="low")
    assert len(out.inline) == 1
    assert out.inline[0].severity == "high" and out.inline[0].category == "security"


def test_same_line_same_category_dedups_regardless_of_message():
    a = mk(line=2, msg="message one")
    b = mk(line=2, msg="completely different words entirely")
    out = apply_dedup([a, b], files(), threshold="low")
    assert len(out.inline) == 1


def test_different_messages_different_categories_both_survive():
    a = mk(line=2, cat="correctness", msg="ZeroDivisionError when count is 0")
    b = mk(line=2, cat="style", msg="function lacks a docstring per repo convention")
    out = apply_dedup([a, b], files(), threshold="low")
    assert len(out.inline) == 2


def test_unanchorable_goes_to_summary():
    out = apply_dedup([mk(path="nope.py", line=1)], files(), threshold="low")
    assert out.inline == [] and len(out.summary_only) == 1


def test_cap_seven_by_severity_then_category():
    # Use 11-line diff so same-cat findings can be spaced >LINE_WINDOW apart (no dedup within groups).
    # Three distinct categories so cross-group similarity check (low ratio) never triggers.
    long_files = parse_diff(LONG_FILE_DIFF)
    findings = (
        [mk(line=1 + i * 4, sev="high", cat="security", msg=f"s{i}") for i in range(3)]
        + [mk(line=2 + i * 4, sev="high", cat="correctness", msg=f"c{i}") for i in range(3)]
        + [mk(line=3 + i * 4, sev="low", cat="style", msg=f"u{i}") for i in range(3)]
    )
    out = apply_dedup(findings, long_files, threshold="low", max_inline=7)
    assert len(out.inline) == 7
    assert [f.severity for f in out.inline][:6] == ["high"] * 6
    assert out.inline[0].category == "security"
    assert len(out.summary_only) == 2


def test_snapping_applied_before_grouping():
    a = mk(line=2)
    b = mk(line=7, msg="division by zero risk!")  # snaps to 5... then |5-2|>3 -> kept
    out = apply_dedup([a, b], files(), threshold="low")
    assert len(out.inline) == 2
    assert {f.line for f in out.inline} == {2, 5}
