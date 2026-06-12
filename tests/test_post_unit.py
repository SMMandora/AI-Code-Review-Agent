from codereview.agent.nodes.post import anchor_findings, format_comment
from codereview.agent.state import Finding
from codereview.diff import parse_diff
from tests.diff_fixtures import NEW_FILE_DIFF


def mk(path="app/util.py", line=2, sev="medium", cat="correctness", msg="m", sug=None):
    return Finding(path=path, line=line, severity=sev, message=msg, suggestion=sug, category=cat)


def test_anchor_snaps_and_orders_by_severity():
    files = parse_diff(NEW_FILE_DIFF)
    findings = [mk(line=2, sev="low"), mk(line=8, sev="high"), mk(path="nope.py", line=1)]
    inline, summary = anchor_findings(findings, files)
    assert [f.severity for f in inline] == ["high", "low"]
    assert inline[0].line == 5  # snapped from 8
    assert summary[0].path == "nope.py"


def test_anchor_caps_at_seven():
    files = parse_diff(NEW_FILE_DIFF)
    findings = [mk(line=n % 5 + 1, msg=f"f{n}") for n in range(10)]
    inline, summary = anchor_findings(findings, files)
    assert len(inline) == 7 and len(summary) == 3


def test_format_comment_with_suggestion_containing_backticks():
    f = mk(sug="x = `weird`")
    out = format_comment(f)
    assert "suggestion" in out and "x = `weird`" in out
    assert "**[medium] correctness**" in out
