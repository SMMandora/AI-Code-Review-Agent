from fnmatch import fnmatch
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from codereview.agent.cost import PRICES_PER_MTOK


class RepoConfig(BaseModel):
    """Validated form of .codereview.yml (spec §4). Loader added in Task 20."""

    skip_files: list[str] = Field(default_factory=list)
    custom_rules: list[str] = Field(default_factory=list)
    model: str = "claude-sonnet-4-6"
    severity_threshold: Literal["low", "medium", "high"] = "low"
    warnings: list[str] = Field(default_factory=list)  # loader-populated, shown in summary

    @field_validator("model")
    @classmethod
    def _known_model(cls, v: str) -> str:
        if v not in PRICES_PER_MTOK:
            raise ValueError(f"model must be one of {sorted(PRICES_PER_MTOK)}")
        return v

    def skips(self, path: str) -> bool:
        return any(fnmatch(path, pattern) for pattern in self.skip_files)
