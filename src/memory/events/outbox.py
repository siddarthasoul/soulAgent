from typing import Any
from uuid import uuid4

from src.memory.storage.database import get_pool


class EventOutboxRepository:
    def claim_one(
        self,
        lease_seconds: int = 60,
        event_types: list[str] | None = None,
        max_attempts: int = 10,
    ) -> dict[str, Any] | None:
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least 1")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if event_types is not None and not event_types:
            return None

        with get_pool().connection() as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    # Exhausted events must not remain eligible for delivery.
                    cursor.execute(
                        """
                        UPDATE event_outbox AS o
                        SET status = 'failed',
                            claimed_at = NULL,
                            claim_token = NULL,
                            last_error = COALESCE(
                                o.last_error,
                                'Maximum delivery attempts exhausted'
                            )
                        FROM memory_events AS e
                        WHERE e.event_id = o.event_id
                          AND o.attempts >= %s
                          AND (
                              o.status = 'pending'
                              OR (
                                  o.status = 'processing'
                                  AND (
                                      o.claimed_at IS NULL
                                      OR o.claimed_at <
                                          NOW() - (
                                              %s * INTERVAL '1 second'
                                          )
                                  )
                              )
                          )
                          AND (
                              %s::text[] IS NULL
                              OR e.event_type = ANY(%s::text[])
                          )
                        """,
                        (
                            max_attempts,
                            lease_seconds,
                            event_types,
                            event_types,
                        ),
                    )

                    cursor.execute(
                        """
                        SELECT
                            o.event_id,
                            o.attempts,
                            e.event_type,
                            e.task_id,
                            e.request_id,
                            e.experience_id,
                            e.strategy_id,
                            e.attempt_id,
                            e.occurred_at,
                            e.payload,
                            e.schema_version,
                            e.source
                        FROM event_outbox AS o
                        JOIN memory_events AS e
                          ON e.event_id = o.event_id
                        WHERE (
                            (
                                o.status = 'pending'
                                AND o.next_attempt_at <= NOW()
                            )
                            OR (
                                o.status = 'processing'
                                AND (
                                    o.claimed_at IS NULL
                                    OR o.claimed_at <
                                        NOW() - (
                                            %s * INTERVAL '1 second'
                                        )
                                )
                                AND o.attempts < %s
                            )
                        )
                        AND (
                            %s::text[] IS NULL
                            OR e.event_type = ANY(%s::text[])
                        )
                        ORDER BY o.next_attempt_at, o.created_at
                        FOR UPDATE OF o SKIP LOCKED
                        LIMIT 1
                        """,
                        (
                            lease_seconds,
                            max_attempts,
                            event_types,
                            event_types,
                        ),
                    )

                    row = cursor.fetchone()
                    if row is None:
                        return None

                    columns = [
                        column.name for column in cursor.description
                    ]
                    event = dict(zip(columns, row, strict=True))
                    claim_token = str(uuid4())

                    cursor.execute(
                        """
                        UPDATE event_outbox
                        SET status = 'processing',
                            attempts = attempts + 1,
                            claimed_at = NOW(),
                            claim_token = %s
                        WHERE event_id = %s
                        """,
                        (claim_token, event["event_id"]),
                    )

                    event["attempts"] += 1
                    event["claim_token"] = claim_token
                    return event

    def mark_delivered(
        self,
        event_id: str,
        claim_token: str,
    ) -> None:
        with get_pool().connection() as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE event_outbox
                        SET status = 'delivered',
                            delivered_at = NOW(),
                            last_error = NULL,
                            claimed_at = NULL,
                            claim_token = NULL
                        WHERE event_id = %s
                          AND status = 'processing'
                          AND claim_token = %s
                        """,
                        (event_id, claim_token),
                    )
                    if cursor.rowcount != 1:
                        raise RuntimeError(
                            f"Could not mark event {event_id} as delivered: "
                            "claim is no longer owned by this worker"
                        )

    def schedule_retry(
        self,
        event_id: str,
        claim_token: str,
        error: str,
        retry_delay_seconds: int = 5,
        max_attempts: int = 10,
    ) -> None:
        if retry_delay_seconds < 0:
            raise ValueError(
                "retry_delay_seconds cannot be negative"
            )
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        with get_pool().connection() as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE event_outbox
                        SET status = CASE
                                WHEN attempts >= %s THEN 'failed'
                                ELSE 'pending'
                            END,
                            next_attempt_at =
                                NOW() + (
                                    %s * INTERVAL '1 second'
                                ),
                            last_error = %s,
                            claimed_at = NULL,
                            claim_token = NULL
                        WHERE event_id = %s
                          AND status = 'processing'
                          AND claim_token = %s
                        """,
                        (
                            max_attempts,
                            retry_delay_seconds,
                            error[:4000],
                            event_id,
                            claim_token,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise RuntimeError(
                            f"Could not schedule retry for event {event_id}: "
                            "claim is no longer owned by this worker"
                        )
