from codereview.agent.nodes.post import format_comment
from codereview.agent.state import Finding


def mk(path="app/util.py", line=2, sev="medium", cat="correctness", msg="m", sug=None):
    return Finding(path=path, line=line, severity=sev, message=msg, suggestion=sug, category=cat)


def test_format_comment_with_suggestion_containing_backticks():
    f = mk(sug="x = `weird`")
    out = format_comment(f)
    assert "suggestion" in out and "x = `weird`" in out
    assert "**[medium] correctness**" in out
