from codereview.agent.nodes.checks import make_check_node
from codereview.agent.state import AgentDeps, ModelFinding, PRMeta
from codereview.diff import parse_diff
from codereview.repo_config import RepoConfig
from tests.diff_fixtures import NEW_FILE_DIFF
from tests.fakes import FakeAnthropic, invalid_parse_response, parse_response


def make_state():
    return {
        "pr": PRMeta(7, "Add util", "", "alice", "abc123", "main", "main"),
        "diff_files": parse_diff(NEW_FILE_DIFF),
        "file_contents": {},
        "config": RepoConfig(),
    }


def make_deps(settings, anthropic):
    return AgentDeps(settings=settings, gh=None, anthropic=anthropic, reviews=None)


async def test_happy_path_stamps_category_and_usage(settings):
    finding = ModelFinding(path="app/util.py", line=2, severity="high", message="ZeroDivisionError when count=0")
    fake = FakeAnthropic([parse_response([finding], input_tokens=1234, output_tokens=56)])
    node = make_check_node("correctness", make_deps(settings, fake))
    out = await node(make_state())
    assert len(out["findings"]) == 1
    f = out["findings"][0]
    assert f.category == "correctness" and f.line == 2
    [u] = out["usage"]
    assert u.node == "correctness" and u.input_tokens == 1234 and u.output_tokens == 56
    call = fake.calls[0]
    assert call["model"] == "claude-sonnet-4-6"
    assert call["thinking"] == {"type": "adaptive"}
    assert call["max_tokens"] == 4000
    assert "UNTRUSTED" in call["messages"][0]["content"]
    assert "correctness" in call["system"]


async def test_long_message_truncated_to_600(settings):
    finding = ModelFinding(path="app/util.py", line=1, severity="low", message="x" * 900)
    fake = FakeAnthropic([parse_response([finding])])
    node = make_check_node("correctness", make_deps(settings, fake))
    out = await node(make_state())
    assert len(out["findings"][0].message) == 600


async def test_validation_failure_retries_once_then_succeeds(settings):
    good = ModelFinding(path="app/util.py", line=2, severity="medium", message="ok")
    fake = FakeAnthropic([invalid_parse_response(), parse_response([good])])
    node = make_check_node("correctness", make_deps(settings, fake))
    out = await node(make_state())
    assert len(out["findings"]) == 1
    assert len(fake.calls) == 2
    assert "failed schema validation" in fake.calls[1]["messages"][0]["content"]


async def test_double_failure_fails_soft(settings):
    fake = FakeAnthropic([RuntimeError("api down"), RuntimeError("api down")])
    node = make_check_node("security", make_deps(settings, fake))
    out = await node(make_state())
    assert "findings" not in out or out["findings"] == []
    [err] = out["errors"]
    assert err.node == "security"
    [u] = out["usage"]
    assert u.input_tokens == 0 and u.output_tokens == 0
