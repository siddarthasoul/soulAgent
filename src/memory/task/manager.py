
from uuid import uuid4
from typing import Any

from src.memory.events import (
    MemoryEvent,
    MemoryEventPublisher,
    MemoryEventType,
)
from src.memory.storage.database import get_pool
from src.memory.task.models import TaskState, TaskStatus, utc_now
from src.memory.task.repository import TaskRepository


class TaskManager:
    def __init__(
        self,
        repository: TaskRepository | None = None,
        event_publisher: MemoryEventPublisher | None = None,
    ) -> None:
        self.repository = repository or TaskRepository()
        self.event_publisher = event_publisher or MemoryEventPublisher()

    def create_task(
        self,
        objective: str,
        request_id: str | None = None,
        pending_steps: list[str] | None = None,
        metadata: dict[str, object] | None = None,
        connection=None,
    ) -> TaskState:
        if not objective.strip():
            raise ValueError("Task objective cannot be empty")

        task = TaskState(
            task_id=str(uuid4()),
            request_id=request_id,
            objective=objective,
            pending_steps=list(pending_steps or []),
            metadata=dict(metadata or {}),
        )

        # IntelligenceController persists TASK_CREATED atomically.
        self.repository.save(task, connection=connection)
        return task

    def get_task(self, task_id: str) -> TaskState | None:
        return self.repository.get(task_id)


    def _transition_task(
        self,
        task_id: str,
        event_type: MemoryEventType,
        mutate,
    ) -> TaskState:
        event = None

        with get_pool().connection() as connection:
            with connection.transaction():
                task = self.repository.get(
                    task_id,
                    connection=connection,
                    for_update=True,
                )

                if task is None:
                    raise KeyError(f"Task not found: {task_id}")

                payload = mutate(task)
                task.updated_at = utc_now()

                event = MemoryEvent(
                    event_type=event_type,
                    task_id=task.task_id,
                    request_id=task.request_id,
                    payload={
                        "status": task.status.value,
                        "current_step": task.current_step,
                        **(payload or {}),
                    },
                )

                self.repository.save(task, connection=connection)
                self.event_publisher.persist(
                    event,
                    connection=connection,
                )

        # The transaction has committed before subscribers are notified.
        self.event_publisher.notify(event)
        return task

    def start_task(self, task_id: str) -> TaskState:
        def mutate(task: TaskState) -> dict[str, Any]:
            if task.status not in (TaskStatus.PENDING, TaskStatus.PAUSED):
                raise ValueError(
                    f"Cannot start a task with status '{task.status.value}'"
                )

            task.status = TaskStatus.RUNNING
            task.attempt_count += 1
            task.last_error = None
            return {"attempt_count": task.attempt_count}

        return self._transition_task(
            task_id, MemoryEventType.TASK_STARTED, mutate
        )

    def start_step(self, task_id: str, step: str) -> TaskState:
        def mutate(task: TaskState) -> dict[str, Any]:
            self._require_running(task)
            if step not in task.pending_steps:
                raise ValueError(f"Step is not pending: {step}")

            task.current_step = step
            return {"step": step}

        return self._transition_task(
            task_id, MemoryEventType.TASK_STEP_STARTED, mutate
        )

    def complete_step(self, task_id: str, step: str) -> TaskState:
        def mutate(task: TaskState) -> dict[str, Any]:
            self._require_running(task)
            if task.current_step != step:
                raise ValueError("Step is not the current step")
            if step not in task.pending_steps:
                raise ValueError(f"Step is not pending: {step}")

            task.completed_steps.append(step)
            task.pending_steps.remove(step)
            task.current_step = None
            return {"step": step}

        return self._transition_task(
            task_id, MemoryEventType.TASK_STEP_COMPLETED, mutate
        )

    def pause_task(
        self, task_id: str, reason: str | None = None
    ) -> TaskState:
        def mutate(task: TaskState) -> dict[str, Any]:
            self._require_running(task)
            task.status = TaskStatus.PAUSED
            task.last_error = reason
            return {"reason": reason}

        return self._transition_task(
            task_id, MemoryEventType.TASK_PAUSED, mutate
        )

    def fail_task(self, task_id: str, reason: str) -> TaskState:
        def mutate(task: TaskState) -> dict[str, Any]:
            self._require_running(task)
            task.status = TaskStatus.FAILED
            task.last_error = reason
            return {"reason": reason}

        return self._transition_task(
            task_id, MemoryEventType.TASK_FAILED, mutate
        )

    def complete_task(self, task_id: str) -> TaskState:
        def mutate(task: TaskState) -> dict[str, Any]:
            self._require_running(task)
            if task.current_step is not None or task.pending_steps:
                raise ValueError(
                    "Cannot complete a task with unfinished steps"
                )

            task.status = TaskStatus.COMPLETED
            return {}

        return self._transition_task(
            task_id, MemoryEventType.TASK_COMPLETED, mutate
        )

    @staticmethod
    def _require_running(task: TaskState) -> None:
        if task.status != TaskStatus.RUNNING:
            raise ValueError(
                f"Task must be running, got '{task.status.value}'"
            )
