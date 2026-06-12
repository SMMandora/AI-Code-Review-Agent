from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True)
class ReviewRecord:
    repo: str
    pr_number: int
    head_sha: str
    status: str  # queued|running|completed|skipped|failed|cost_exceeded
    trigger: str
    model: str
    findings_total: int = 0
    comments_posted: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    error: str | None = None


class ReviewStore(Protocol):
    async def record(self, r: ReviewRecord) -> None: ...
    async def has_completed(self, repo: str, pr_number: int, head_sha: str) -> bool: ...
    async def recent(self, limit: int = 50) -> list[dict]: ...


@dataclass
class InMemoryReviewStore:
    rows: list[tuple[ReviewRecord, datetime]] = field(default_factory=list)

    async def record(self, r: ReviewRecord) -> None:
        self.rows.append((r, datetime.now(UTC)))

    async def has_completed(self, repo: str, pr_number: int, head_sha: str) -> bool:
        return any(
            r.repo == repo and r.pr_number == pr_number and r.head_sha == head_sha
            and r.status == "completed"
            for r, _ in self.rows
        )

    async def recent(self, limit: int = 50) -> list[dict]:
        out = [{**asdict(r), "created_at": ts} for r, ts in reversed(self.rows)]
        return out[:limit]
