from uuid import uuid4
from typing import Any

from src.memory.experience.models import (
    EvidenceRecord,
    ExperienceOutcome,
    ExperienceRecord,
    ExperienceStatus,
)


class ExperienceAnalyzer:
    """Convert execution observations into structured experiences."""

    def analyze(
        self,
        *,
        query: str,
        problem_pattern: str,
        diagnosis: str,
        action: str,
        outcome: ExperienceOutcome = ExperienceOutcome.UNKNOWN,
        task_id: str | None = None,
        request_id: str | None = None,
        task_type: str | None = None,
        context: dict[str, Any] | None = None,
        evidence: list[EvidenceRecord] | None = None,
        confidence: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ExperienceRecord:
        required_fields = {
            "query": query,
            "problem_pattern": problem_pattern,
            "diagnosis": diagnosis,
            "action": action,
        }

        for field_name, value in required_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{field_name} must be a non-empty string"
                )

        return ExperienceRecord(
            experience_id=str(uuid4()),
            task_id=task_id,
            request_id=request_id,
            query=query.strip(),
            task_type=task_type,
            problem_pattern=problem_pattern.strip(),
            context=context or {},
            diagnosis=diagnosis.strip(),
            action=action.strip(),
            outcome=outcome,
            evidence=evidence or [],
            status=ExperienceStatus.CANDIDATE,
            confidence=confidence,
            metadata=metadata or {},
        )
