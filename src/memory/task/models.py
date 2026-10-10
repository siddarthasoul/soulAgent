from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskState(BaseModel):
    task_id: str
    request_id: str | None = None

    objective: str
    status: TaskStatus = TaskStatus.PENDING

    current_step: str | None = None
    completed_steps: list[str] = Field(default_factory=list)
    pending_steps: list[str] = Field(default_factory=list)

    attempt_count: int = 0
    last_error: str | None = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    metadata: dict[str, object] = Field(default_factory=dict)
