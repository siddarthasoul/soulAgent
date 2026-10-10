from typing import Any

from src.memory.events import (
    MemoryEvent,
    MemoryEventPublisher,
    MemoryEventType,
)
from src.memory.experience.analyzer import ExperienceAnalyzer
from src.memory.experience.models import (
    EvidenceRecord,
    ExperienceOutcome,
    ExperienceRecord,
    ExperienceStatus
)
from src.memory.experience.repository import ExperienceRepository
from src.memory.experience.retriever import ExperienceRetriever
from src.memory.strategy.manager import StrategyManager
from src.memory.strategy.selector import (
    StrategyRecommendation,
    StrategySelector,
)
from src.memory.strategy.models import StrategyOutcome
from src.memory.task.manager import TaskManager
from src.memory.task.models import TaskState

from src.memory.storage.database import get_pool


class IntelligenceController:
    """Coordinate task, experience, strategy, and event memory."""

    def __init__(
        self,
        task_manager: TaskManager | None = None,
        experience_repository: ExperienceRepository | None = None,
        strategy_manager: StrategyManager | None = None,
        event_publisher: MemoryEventPublisher | None = None,
    ) -> None:

        self.event_publisher = event_publisher or MemoryEventPublisher()

        self.task_manager = task_manager or TaskManager(
            event_publisher=self.event_publisher
        )

        self.experience_repository = (
            experience_repository or ExperienceRepository()
        )
        self.experience_analyzer = ExperienceAnalyzer()
        self.experience_retriever = ExperienceRetriever(
            self.experience_repository
        )

        self.strategy_manager = strategy_manager or StrategyManager()
        self.strategy_selector = StrategySelector(self.strategy_manager)




    def create_task(
        self,
        objective: str,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskState:
        event = None

        with get_pool().connection() as connection:
            with connection.transaction():
                task = self.task_manager.create_task(
                    objective=objective,
                    request_id=request_id,
                    metadata=metadata,
                    connection=connection,
                )

                event = MemoryEvent(
                    event_type=MemoryEventType.TASK_CREATED,
                    task_id=task.task_id,
                    request_id=task.request_id,
                    payload={
                        "objective": task.objective,
                        "status": task.status.value,
                    },
                )

                self.event_publisher.persist(
                    event,
                    connection=connection,
                )


        self.event_publisher.notify(event)

        return task


    def get_task(self, task_id: str) -> TaskState:
        return self.task_manager.get_task(task_id)

    def record_experience(
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
        experience = self.experience_analyzer.analyze(
            query=query,
            problem_pattern=problem_pattern,
            diagnosis=diagnosis,
            action=action,
            outcome=outcome,
            task_id=task_id,
            request_id=request_id,
            task_type=task_type,
            context=context,
            evidence=evidence,
            confidence=confidence,
            metadata=metadata,
        )

        event = MemoryEvent(
            event_type=MemoryEventType.EXPERIENCE_RECORDED,
            task_id=experience.task_id,
            request_id=experience.request_id,
            experience_id=experience.experience_id,
            payload={
                "problem_pattern": experience.problem_pattern,
                "outcome": experience.outcome.value,
                "status": experience.status.value,
            },
        )

        with get_pool().connection() as connection:
            with connection.transaction():
                self.experience_repository.save(
                    experience,
                    connection=connection,
                )
                self.event_publisher.persist(
                    event,
                    connection=connection,
                )

        # Notify subscribers only after the transaction commits.
        self.event_publisher.notify(event)
        return experience

    def learn_from_task(
        self,
        *,
        task_id: str,
        diagnosis: str,
        action: str,
        outcome: ExperienceOutcome,
        problem_pattern: str,
        evidence: list[EvidenceRecord] | None = None,
        strategy_id: str | None = None,
        verified: bool = False,
        confidence: float = 0.0,
        operation_key: str | None = None,
    ) -> ExperienceRecord:


        if not action.strip():
            raise ValueError("Action cannot be empty")

        if verified and outcome == ExperienceOutcome.UNKNOWN:
            raise ValueError("An unknown outcome cannot be marked verified")

        if verified and (
            not evidence
            or not any(item.supports_outcome for item in evidence)
        ):
            raise ValueError("Verified learning requires supporting evidence")

        if operation_key is not None and not operation_key.strip():
            raise ValueError("operation_key cannot be empty")

        evidence_payload = []
        for item in evidence or []:
            recorded_at = getattr(item, "recorded_at", None)
            evidence_payload.append({
                "evidence_type": str(
                    getattr(item.evidence_type, "value", item.evidence_type)
                ),
                "description": item.description,
                "source": getattr(item, "source", None),
                "supports_outcome": item.supports_outcome,
                "recorded_at": (
                    recorded_at.isoformat()
                    if hasattr(recorded_at, "isoformat")
                    else str(recorded_at) if recorded_at is not None else None
                ),
            })

        fingerprint_payload = {
            "task_id": task_id,
            "diagnosis": diagnosis,
            "action": action,
            "outcome": outcome.value,
            "problem_pattern": problem_pattern,
            "evidence": evidence_payload,
            "strategy_id": strategy_id,
            "verified": verified,
            "confidence": confidence,
        }

        import hashlib
        import json

        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_payload,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest()

        key = operation_key.strip() if operation_key else f"auto:{fingerprint}"

        strategy_outcome = {
            ExperienceOutcome.SUCCESS: StrategyOutcome.SUCCESS,
            ExperienceOutcome.FAILURE: StrategyOutcome.FAILURE,
            ExperienceOutcome.PARTIAL: StrategyOutcome.PARTIAL,
            ExperienceOutcome.UNKNOWN: StrategyOutcome.UNKNOWN,
        }[outcome]

        events: list[MemoryEvent] = []
        duplicate_experience_id = None

        with get_pool().connection() as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    # Serialize concurrent retries using the same operation key.
                    cursor.execute(
                        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                        (key,),
                    )
                    cursor.execute(
                        """
                        SELECT fingerprint, experience_id
                        FROM learning_operations
                        WHERE operation_key = %s
                        """,
                        (key,),
                    )
                    existing = cursor.fetchone()

                    if existing:
                        old_fingerprint, duplicate_experience_id = existing
                        if old_fingerprint != fingerprint:
                            raise ValueError(
                                "operation_key was reused with different input"
                            )
                    else:
                        task = self.task_manager.repository.get(
                            task_id,
                            connection=connection,
                            for_update=True,
                        )
                        if task is None:
                            raise ValueError(f"Task not found: {task_id}")

                        if task.status.value not in {"completed", "failed"}:
                            raise ValueError(
                                "Learning requires a completed or failed task"
                            )
                        experience = self.experience_analyzer.analyze(
                            query=task.objective,
                            problem_pattern=problem_pattern,
                            diagnosis=diagnosis,
                            action=action,
                            outcome=outcome,
                            task_id=task.task_id,
                            request_id=task.request_id,
                            task_type=str(
                                task.metadata.get("task_type", "general")
                            ),
                            context={"task_status": task.status.value},
                            evidence=evidence,
                            confidence=confidence,
                            metadata={"strategy_id": strategy_id}
                            if strategy_id else {},
                        )

                        self.experience_repository.save(
                            experience,
                            connection=connection,
                        )

                        attempt = None
                        if strategy_id is not None:
                            attempt = self.strategy_manager.record_attempt(
                                strategy_id=strategy_id,
                                task_id=task.task_id,
                                action_taken=action,
                                outcome=(
                                    strategy_outcome
                                    if verified
                                    else StrategyOutcome.UNKNOWN
                                ),
                                observation=diagnosis,
                                evidence=[
                                    item.description
                                    for item in (evidence or [])
                                    if item.supports_outcome
                                ],
                                verified=verified,
                                connection=connection,
                            )

                        cursor.execute(
                            """
                            INSERT INTO learning_operations (
                                operation_key,
                                fingerprint,
                                experience_id,
                                attempt_id
                            )
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                key,
                                fingerprint,
                                experience.experience_id,
                                attempt.attempt_id if attempt else None,
                            ),
                        )

                        events.append(
                            MemoryEvent(
                                event_type=MemoryEventType.EXPERIENCE_RECORDED,
                                task_id=task.task_id,
                                request_id=task.request_id,
                                experience_id=experience.experience_id,
                                strategy_id=strategy_id,
                                payload={
                                    "outcome": outcome.value,
                                    "status": experience.status.value,
                                    "verified_for_strategy": verified,
                                },
                            )
                        )

                        if attempt is not None:
                            events.append(
                                MemoryEvent(
                                    event_type=(
                                        MemoryEventType.STRATEGY_ATTEMPT_VERIFIED
                                        if verified
                                        else MemoryEventType.STRATEGY_ATTEMPT_RECORDED
                                    ),
                                    task_id=task.task_id,
                                    request_id=task.request_id,
                                    experience_id=experience.experience_id,
                                    strategy_id=strategy_id,
                                    attempt_id=attempt.attempt_id,
                                    payload={
                                        "outcome": attempt.outcome.value,
                                        "verified": attempt.verified,
                                    },
                                )
                            )

                        # Event and outbox persistence share the learning transaction.
                        for event in events:
                            self.event_publisher.persist(
                                event,
                                connection=connection,
                            )

        # The database transaction has committed at this point.
        if duplicate_experience_id is not None:
            existing_experience = self.experience_repository.get(
                duplicate_experience_id
            )
            if existing_experience is None:
                raise RuntimeError(
                    "Learning operation exists but its experience is missing"
                )
            return existing_experience

        # Never notify subscribers before the database commit.
        for event in events:
            self.event_publisher.notify(event)

        return experience

    def retrieve_experiences(
        self,
        query: str,
        *,
        problem_pattern: str | None = None,
        verified_only: bool = True,
        limit: int = 5,
    ) -> list[ExperienceRecord]:
        return self.experience_retriever.search(
            query=query,
            problem_pattern=problem_pattern,
            verified_only=verified_only,
            limit=limit,
        )

    def recommend_strategies(
        self,
        *,
        task_type: str,
        problem_pattern: str | None = None,
        limit: int = 3,
    ) -> list[StrategyRecommendation]:
        return self.strategy_selector.select(
            task_type=task_type,
            problem_pattern=problem_pattern,
            limit=limit,
        )
