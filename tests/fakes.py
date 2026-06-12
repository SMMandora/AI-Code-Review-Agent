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


class FakeVoyage:
    """Duck-type of voyageai.AsyncClient."""

    def __init__(self, dim: int = 4, fail_times: int = 0) -> None:
        self.dim = dim
        self.calls: list[tuple[list[str], str, str]] = []
        self._fail = fail_times

    async def embed(self, texts, model, input_type, **kwargs):
        if self._fail > 0:
            self._fail -= 1
            raise RuntimeError("503 from voyage")
        self.calls.append((list(texts), model, input_type))
        return SimpleNamespace(
            embeddings=[[float(len(t) % 97)] * self.dim for t in texts]
        )
