import logging
from fnmatch import fnmatch
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from codereview.agent.cost import PRICES_PER_MTOK

log = logging.getLogger(__name__)

CONFIG_PATH = ".codereview.yml"
KNOWN_KEYS = {"skip_files", "custom_rules", "model", "severity_threshold"}


class RepoConfig(BaseModel):
    """Validated form of .codereview.yml (spec §4)."""

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
        # fnmatch, not gitignore: `*` crosses `/` (so `*.lock` matches at any depth),
        # while `dist/**` anchors at the repo root and does NOT match `pkg/dist/...`.
        return any(fnmatch(path, pattern) for pattern in self.skip_files)


async def load_repo_config(gh, ref: str, default_model: str) -> "RepoConfig":
    """Fetch + validate .codereview.yml from the target repo (spec §4).

    Invalid input never fails the review: fall back to defaults + warnings
    that surface in the review summary.
    """
    warnings: list[str] = []
    raw = await gh.get_file(CONFIG_PATH, ref)
    if raw is None:
        return RepoConfig(model=default_model)

    def label(text: object) -> str:
        # repo-controlled text lands in the review body markdown — neutralize it
        return " ".join(str(text).replace("`", "'").split())[:120]

    try:
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            raise ValueError("top level must be a mapping")
    except Exception as exc:
        warnings.append(f"`.codereview.yml` could not be parsed ({label(exc)}); using defaults.")
        return RepoConfig(model=default_model, warnings=warnings)

    # non-string keys (yaml `1:` / `true:`) are unknown by definition and would
    # crash RepoConfig(**data) with a TypeError if left in
    unknown = sorted(
        (k for k in data if not (isinstance(k, str) and k in KNOWN_KEYS)), key=str
    )
    for key in unknown:
        warnings.append(f"`.codereview.yml` unknown key `{label(key)}` ignored.")
        data.pop(key, None)

    data.setdefault("model", default_model)
    try:
        cfg = RepoConfig(**data, warnings=warnings)
    except ValidationError as exc:
        fields = ", ".join(str(e["loc"][0]) for e in exc.errors())
        warnings.append(f"`.codereview.yml` has invalid value(s) for: {fields}; using defaults.")
        cfg = RepoConfig(model=default_model, warnings=warnings)
    return cfg
