from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryEventType(str, Enum):
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_STEP_STARTED = "task.step_started"
    TASK_STEP_COMPLETED = "task.step_completed"
    TASK_PAUSED = "task.paused"
    TASK_FAILED = "task.failed"
    TASK_COMPLETED = "task.completed"

    EXPERIENCE_RECORDED = "experience.recorded"
    EXPERIENCE_VERIFIED = "experience.verified"

    STRATEGY_REGISTERED = "strategy.registered"
    STRATEGY_ATTEMPT_RECORDED = "strategy.attempt_recorded"
    STRATEGY_ATTEMPT_VERIFIED = "strategy.attempt_verified"
    STRATEGY_EVALUATED = "strategy.evaluated"


class MemoryEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: MemoryEventType

    task_id: str | None = None
    request_id: str | None = None
    experience_id: str | None = None
    strategy_id: str | None = None
    attempt_id: str | None = None

    occurred_at: datetime = Field(default_factory=utc_now)

    # Store structured, JSON-compatible event details here.
    payload: dict[str, Any] = Field(default_factory=dict)

    # Enables future routing, tracing, and schema evolution.
    schema_version: int = Field(default=1, ge=1)
    source: str = "soul.memory"
