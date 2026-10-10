from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExperienceOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class ExperienceStatus(str, Enum):
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    REJECTED = "rejected"


class EvidenceType(str, Enum):
    TEST_RESULT = "test_result"
    EXECUTION_RESULT = "execution_result"
    TOOL_RESULT = "tool_result"
    HUMAN_FEEDBACK = "human_feedback"
    LLM_ASSESSMENT = "llm_assessment"
    OTHER = "other"


class EvidenceRecord(BaseModel):
    evidence_type: EvidenceType
    description: str
    source: str | None = None
    supports_outcome: bool = True
    recorded_at: datetime = Field(default_factory=utc_now)


class ExperienceRecord(BaseModel):
    experience_id: str
    task_id: str | None = None
    request_id: str | None = None

    query: str
    task_type: str | None = None
    problem_pattern: str

    context: dict[str, object] = Field(default_factory=dict)
    diagnosis: str
    action: str

    outcome: ExperienceOutcome = ExperienceOutcome.UNKNOWN
    evidence: list[EvidenceRecord] = Field(default_factory=list)

    # New experiences are candidates until a separate verification
    # process establishes that the lesson is supported by evidence.
    status: ExperienceStatus = ExperienceStatus.CANDIDATE
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, object] = Field(default_factory=dict)
