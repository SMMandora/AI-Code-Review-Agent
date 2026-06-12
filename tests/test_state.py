import pytest
from pydantic import ValidationError

from codereview.agent.state import CheckResult, Finding, ModelFinding


def test_model_finding_validates_severity():
    with pytest.raises(ValidationError):
        ModelFinding(path="a.py", line=1, severity="critical", message="m")


def test_check_result_defaults_empty():
    assert CheckResult().findings == []


def test_finding_extends_model_finding_with_category():
    mf = ModelFinding(path="a.py", line=3, severity="high", message="m", suggestion="x = 1")
    f = Finding(**mf.model_dump(), category="security")
    assert f.category == "security" and f.line == 3 and f.suggestion == "x = 1"
