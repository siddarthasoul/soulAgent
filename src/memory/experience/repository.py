
from pathlib import Path

from psycopg.types.json import Jsonb

from src.memory.experience.models import (
    EvidenceRecord,
    ExperienceRecord,
    ExperienceStatus,
)
from src.memory.storage.database import get_pool


class ExperienceRepository:
    """Persist experiences and their evidence in PostgreSQL."""

    def __init__(self, storage_dir: str | None = None) -> None:
        # Retained for constructor compatibility. PostgreSQL is authoritative.
        self.storage_dir = Path(storage_dir) if storage_dir else None

    def _validate_experience_id(self, experience_id: str) -> None:
        if not experience_id or Path(experience_id).name != experience_id:
            raise ValueError("Invalid experience_id")

    def save(
        self,
        experience: ExperienceRecord,
        *,
        connection=None,
    ) -> None:

        if connection is not None:
            with connection.cursor() as cursor:
                self._save_with_cursor(cursor, experience)
            return

        with get_pool().connection() as conn:
            with conn.transaction():
                with conn.cursor() as cursor:
                    self._save_with_cursor(cursor, experience)

    def _save_with_cursor(self, cursor, experience: ExperienceRecord) -> None:
        self._validate_experience_id(experience.experience_id)

        cursor.execute(
            """
            INSERT INTO experiences (
                experience_id, task_id, request_id, query,
                task_type, problem_pattern, context, diagnosis,
                action, outcome, status, confidence, created_at,
                metadata
            )
            VALUES (
                %(experience_id)s, %(task_id)s, %(request_id)s,
                %(query)s, %(task_type)s, %(problem_pattern)s,
                %(context)s, %(diagnosis)s, %(action)s,
                %(outcome)s, %(status)s, %(confidence)s,
                %(created_at)s, %(metadata)s
            )
            ON CONFLICT (experience_id) DO UPDATE SET
                task_id = EXCLUDED.task_id,
                request_id = EXCLUDED.request_id,
                query = EXCLUDED.query,
                task_type = EXCLUDED.task_type,
                problem_pattern = EXCLUDED.problem_pattern,
                context = EXCLUDED.context,
                diagnosis = EXCLUDED.diagnosis,
                action = EXCLUDED.action,
                outcome = EXCLUDED.outcome,
                status = EXCLUDED.status,
                confidence = EXCLUDED.confidence,
                metadata = EXCLUDED.metadata
            """,
            {
                "experience_id": experience.experience_id,
                "task_id": experience.task_id,
                "request_id": experience.request_id,
                "query": experience.query,
                "task_type": experience.task_type,
                "problem_pattern": experience.problem_pattern,
                "context": Jsonb(experience.context),
                "diagnosis": experience.diagnosis,
                "action": experience.action,
                "outcome": experience.outcome.value,
                "status": experience.status.value,
                "confidence": experience.confidence,
                "created_at": experience.created_at,
                "metadata": Jsonb(experience.metadata),
            },
        )

        # Replace evidence in the same transaction as the experience.
        cursor.execute(
            "DELETE FROM experience_evidence WHERE experience_id = %s",
            (experience.experience_id,),
        )

        if experience.evidence:
            cursor.executemany(
                """
                INSERT INTO experience_evidence (
                    experience_id, evidence_type, description,
                    source, supports_outcome, recorded_at
                )
                VALUES (
                    %(experience_id)s, %(evidence_type)s, %(description)s,
                    %(source)s, %(supports_outcome)s, %(recorded_at)s
                )
                """,
                [
                    {
                        "experience_id": experience.experience_id,
                        "evidence_type": item.evidence_type.value,
                        "description": item.description,
                        "source": item.source,
                        "supports_outcome": item.supports_outcome,
                        "recorded_at": item.recorded_at,
                    }
                    for item in experience.evidence
                ],
            )

    def _get_evidence(
        self,
        connection,
        experience_id: str,
    ) -> list[EvidenceRecord]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT evidence_type, description, source,
                       supports_outcome, recorded_at
                FROM experience_evidence
                WHERE experience_id = %s
                ORDER BY recorded_at, evidence_id
                """,
                (experience_id,),
            )
            rows = cursor.fetchall()

        return [
            EvidenceRecord(
                evidence_type=row[0],
                description=row[1],
                source=row[2],
                supports_outcome=row[3],
                recorded_at=row[4],
            )
            for row in rows
        ]

    def _build_experience(self, connection, row) -> ExperienceRecord:
        columns = (
            "experience_id", "task_id", "request_id", "query",
            "task_type", "problem_pattern", "context", "diagnosis",
            "action", "outcome", "status", "confidence", "created_at",
            "metadata",
        )
        data = dict(zip(columns, row, strict=True))
        data["evidence"] = self._get_evidence(
            connection,
            data["experience_id"],
        )
        return ExperienceRecord.model_validate(data)

    def get(self, experience_id: str) -> ExperienceRecord | None:
        self._validate_experience_id(experience_id)

        with get_pool().connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT experience_id, task_id, request_id, query,
                           task_type, problem_pattern, context, diagnosis,
                           action, outcome, status, confidence, created_at,
                           metadata
                    FROM experiences
                    WHERE experience_id = %s
                    """,
                    (experience_id,),
                )
                row = cursor.fetchone()

            if row is None:
                return None

            return self._build_experience(connection, row)

    def list_experiences(self) -> list[ExperienceRecord]:
        with get_pool().connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT experience_id, task_id, request_id, query,
                           task_type, problem_pattern, context, diagnosis,
                           action, outcome, status, confidence, created_at,
                           metadata
                    FROM experiences
                    ORDER BY created_at, experience_id
                    """
                )
                rows = cursor.fetchall()

            return [
                self._build_experience(connection, row)
                for row in rows
            ]

    def list_verified(self) -> list[ExperienceRecord]:
        with get_pool().connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT experience_id, task_id, request_id, query,
                           task_type, problem_pattern, context, diagnosis,
                           action, outcome, status, confidence, created_at,
                           metadata
                    FROM experiences
                    WHERE status = %s
                    ORDER BY created_at, experience_id
                    """,
                    (ExperienceStatus.VERIFIED.value,),
                )
                rows = cursor.fetchall()

            return [
                self._build_experience(connection, row)
                for row in rows
            ]

    def delete(self, experience_id: str) -> bool:
        self._validate_experience_id(experience_id)

        # The evidence rows are removed by the foreign-key cascade.
        with get_pool().connection() as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM experiences WHERE experience_id = %s",
                        (experience_id,),
                    )
                    return cursor.rowcount > 0