from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StrategyOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class StrategyStatus(str, Enum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    DISABLED = "disabled"


class StrategyRecord(BaseModel):
    strategy_id: str

    name: str
    description: str
    task_type: str
    problem_pattern: str | None = None

    # Ordered actions that describe how the strategy operates.
    steps: list[str] = Field(default_factory=list)

    # Aggregate performance statistics.
    total_attempts: int = Field(default=0, ge=0)
    successes: int = Field(default=0, ge=0)
    failures: int = Field(default=0, ge=0)
    partial_successes: int = Field(default=0, ge=0)
    unknown_outcomes: int = Field(default=0, ge=0)

    status: StrategyStatus = StrategyStatus.CANDIDATE

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    metadata: dict[str, object] = Field(default_factory=dict)


class StrategyAttempt(BaseModel):
    attempt_id: str
    strategy_id: str
    task_id: str | None = None

    outcome: StrategyOutcome = StrategyOutcome.UNKNOWN

    # Explain what was attempted and what actually happened.
    action_taken: str
    observation: str | None = None

    # Evidence should describe observable results, not just model opinions.
    evidence: list[str] = Field(default_factory=list)

    # Whether the outcome was independently checked.
    verified: bool = False

    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, object] = Field(default_factory=dict)
