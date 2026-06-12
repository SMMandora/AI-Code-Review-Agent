from types import SimpleNamespace

from codereview.agent.state import CheckResult, ModelFinding


def parse_response(findings: list[ModelFinding] | None = None, input_tokens: int = 1000, output_tokens: int = 200):
    return SimpleNamespace(
        parsed_output=CheckResult(findings=findings or []),
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def invalid_parse_response(input_tokens: int = 500, output_tokens: int = 50):
    return SimpleNamespace(
        parsed_output=None,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class FakeAnthropic:
    """Duck-type of AsyncAnthropic for tests: queue of responses or exceptions."""

    def __init__(self, responses: list) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []
        self.messages = SimpleNamespace(parse=self._parse)

    async def _parse(self, **kwargs):
        self.calls.append(kwargs)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item
