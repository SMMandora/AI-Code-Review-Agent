import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field

from codereview.diff import DiffFile
from codereview.repo_config import RepoConfig
from codereview.settings import Settings
from codereview.worker import ReviewJob

CATEGORIES = ("correctness", "security", "style", "test_coverage")


class ModelFinding(BaseModel):
    """What the model is asked to emit. category is stamped by the node, never the model."""

    path: str = Field(description="Repository-relative file path exactly as shown in the diff")
    line: int = Field(description="Line number on the NEW side of the diff")
    severity: Literal["low", "medium", "high"] = Field(
        description="high=likely breakage/vulnerability, medium=probable bug, low=minor"
    )
    message: str = Field(description="The issue and why it matters, under 600 characters")
    suggestion: str | None = Field(
        default=None, description="Replacement code for the flagged line(s) only, no prose"
    )


class CheckResult(BaseModel):
    findings: list[ModelFinding] = Field(default_factory=list)


class Finding(ModelFinding):
    category: str = ""


@dataclass(frozen=True)
class PRMeta:
    number: int
    title: str
    body: str
    author: str
    head_sha: str
    base_ref: str
    default_branch: str


@dataclass(frozen=True)
class NodeUsage:
    node: str
    input_tokens: int
    output_tokens: int
    duration_ms: int


@dataclass(frozen=True)
class CheckError:
    node: str
    error: str


@dataclass(frozen=True)
class Snippet:
    source_type: str  # code | style | pr_comment
    path: str
    start_line: int
    end_line: int
    content: str


@dataclass
class RetrievedContext:
    per_file: dict[str, list[Snippet]] = field(default_factory=dict)
    global_snippets: list[Snippet] = field(default_factory=list)


@dataclass
class AgentDeps:
    """Everything nodes need; tests swap in fakes (duck-typed on purpose)."""

    settings: Settings
    gh: Any
    anthropic: Any
    reviews: Any
    retriever: Any = None
    config_loader: Any = None  # async (default_branch: str) -> RepoConfig


class ReviewState(TypedDict, total=False):
    job: ReviewJob
    started_monotonic: float
    pr: PRMeta
    diff_files: list[DiffFile]
    file_contents: dict[str, str]
    config: RepoConfig
    context: RetrievedContext
    findings: Annotated[list[Finding], operator.add]
    usage: Annotated[list[NodeUsage], operator.add]
    errors: Annotated[list[CheckError], operator.add]
    skip_reason: str
    posted: bool
    comments_posted: int
    findings_total: int
