
from pathlib import Path

from psycopg.types.json import Jsonb

from src.memory.storage.database import get_pool
from src.memory.task.models import TaskState


class TaskRepository:
    """Persist task state in PostgreSQL."""

    def __init__(self, storage_dir: str | None = None) -> None:
        # Kept for constructor compatibility with the former JSON repository.
        # PostgreSQL is now the source of truth.
        self.storage_dir = Path(storage_dir) if storage_dir else None

    def _validate_task_id(self, task_id: str) -> None:
        if not task_id or Path(task_id).name != task_id:
            raise ValueError("Invalid task_id")


    def save(self, task: TaskState, *, connection=None) -> None:
        def save_with_cursor(cursor) -> None:
            cursor.execute(
                """
                INSERT INTO tasks (
                    task_id, request_id, objective, status,
                    current_step, completed_steps, pending_steps,
                    attempt_count, last_error, created_at,
                    updated_at, metadata
                )
                VALUES (
                    %(task_id)s, %(request_id)s, %(objective)s,
                    %(status)s, %(current_step)s,
                    %(completed_steps)s, %(pending_steps)s,
                    %(attempt_count)s, %(last_error)s,
                    %(created_at)s, %(updated_at)s, %(metadata)s
                )
                ON CONFLICT (task_id) DO UPDATE SET
                    request_id = EXCLUDED.request_id,
                    objective = EXCLUDED.objective,
                    status = EXCLUDED.status,
                    current_step = EXCLUDED.current_step,
                    completed_steps = EXCLUDED.completed_steps,
                    pending_steps = EXCLUDED.pending_steps,
                    attempt_count = EXCLUDED.attempt_count,
                    last_error = EXCLUDED.last_error,
                    updated_at = EXCLUDED.updated_at,
                    metadata = EXCLUDED.metadata
                """,
                {
                    "task_id": task.task_id,
                    "request_id": task.request_id,
                    "objective": task.objective,
                    "status": task.status.value,
                    "current_step": task.current_step,
                    "completed_steps": Jsonb(task.completed_steps),
                    "pending_steps": Jsonb(task.pending_steps),
                    "attempt_count": task.attempt_count,
                    "last_error": task.last_error,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "metadata": Jsonb(task.metadata),
                },
            )

        if connection is not None:
            with connection.cursor() as cursor:
                save_with_cursor(cursor)
            return

        with get_pool().connection() as conn:
            with conn.transaction():
                with conn.cursor() as cursor:
                    save_with_cursor(cursor)




    def get(
        self,
        task_id: str,
        *,
        connection=None,
        for_update: bool = False,
    ) -> TaskState | None:
        self._validate_task_id(task_id)

        if for_update and connection is None:
            raise ValueError("for_update requires a caller-supplied connection")

        def fetch(cursor):
            query = "SELECT * FROM tasks WHERE task_id = %s"
            if for_update:
                query += " FOR UPDATE"

            cursor.execute(query, (task_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            columns = [column.name for column in cursor.description]
            return TaskState.model_validate(
                dict(zip(columns, row, strict=True))
            )

        if connection is not None:
            with connection.cursor() as cursor:
                return fetch(cursor)

        with get_pool().connection() as conn:
            with conn.cursor() as cursor:
                return fetch(cursor)



    def list_tasks(self) -> list[TaskState]:
        with get_pool().connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM tasks ORDER BY created_at, task_id"
                )
                columns = [column.name for column in cursor.description]
                rows = cursor.fetchall()

        return [
            TaskState.model_validate(dict(zip(columns, row, strict=True)))
            for row in rows
        ]

    def delete(self, task_id: str) -> bool:
        self._validate_task_id(task_id)

        with get_pool().connection() as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM tasks WHERE task_id = %s",
                        (task_id,),
                    )
                    return cursor.rowcount > 0