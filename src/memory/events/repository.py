
from typing import Any

from psycopg.types.json import Jsonb

from src.memory.events.schemas import MemoryEvent
from src.memory.storage.database import get_pool


class MemoryEventRepository:
    """Persist events and their outbox entries."""

    @staticmethod
    def _save_with_cursor(cursor, event: MemoryEvent) -> bool:
        event_data = event.model_dump(mode="json")

        cursor.execute(
            """
            INSERT INTO memory_events (
                event_id, event_type, task_id, request_id,
                experience_id, strategy_id, attempt_id,
                occurred_at, payload, schema_version, source
            )
            VALUES (
                %(event_id)s, %(event_type)s, %(task_id)s,
                %(request_id)s, %(experience_id)s,
                %(strategy_id)s, %(attempt_id)s,
                %(occurred_at)s, %(payload)s,
                %(schema_version)s, %(source)s
            )
            ON CONFLICT (event_id) DO NOTHING
            RETURNING event_id
            """,
            {
                **event_data,
                "event_type": event.event_type.value,
                "payload": Jsonb(event.payload),
            },
        )

        if cursor.fetchone() is None:
            return False

        cursor.execute(
            """
            INSERT INTO event_outbox (event_id)
            VALUES (%s)
            """,
            (event.event_id,),
        )
        return True

    def save(
        self,
        event: MemoryEvent,
        *,
        connection=None,
    ) -> bool:
        """Save the event and outbox row in the caller's transaction if given."""
        if connection is not None:
            with connection.cursor() as cursor:
                return self._save_with_cursor(cursor, event)

        with get_pool().connection() as conn:
            with conn.transaction():
                with conn.cursor() as cursor:
                    return self._save_with_cursor(cursor, event)

    def get_by_id(self, event_id: str) -> dict[str, Any] | None:
        with get_pool().connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        event_id, event_type, task_id, request_id,
                        experience_id, strategy_id, attempt_id,
                        occurred_at, payload, schema_version,
                        source, created_at
                    FROM memory_events
                    WHERE event_id = %s
                    """,
                    (event_id,),
                )

                row = cursor.fetchone()
                if row is None:
                    return None

                columns = [column.name for column in cursor.description]
                return dict(zip(columns, row, strict=True))
