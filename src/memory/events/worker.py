
from collections.abc import Callable
from typing import Any

from src.memory.events.outbox import EventOutboxRepository
from src.memory.events.schemas import MemoryEventType


EventConsumer = Callable[[dict[str, Any]], None]


class EventOutboxWorker:

    def __init__(
        self,
        repository: EventOutboxRepository | None = None,
        *,
        lease_seconds: int = 60,
        retry_delay_seconds: int = 5,
        max_attempts: int = 10,
    ) -> None:
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least 1")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        self._repository = repository or EventOutboxRepository()
        self._lease_seconds = lease_seconds
        self._retry_delay_seconds = retry_delay_seconds
        self._max_attempts = max_attempts
        self._consumers: dict[str, EventConsumer] = {}

    def register_consumer(
        self,
        event_type: MemoryEventType | str,
        consumer: EventConsumer,
    ) -> None:
        key = (
            event_type.value
            if isinstance(event_type, MemoryEventType)
            else event_type
        )

        if not key:
            raise ValueError("event_type cannot be empty")

        self._consumers[key] = consumer

    def run_once(self) -> str:
        """
        Process at most one event.

        Returns 'idle', 'delivered', or 'retry_scheduled'.
        """
        if not self._consumers:
            return "idle"

        event = self._repository.claim_one(
            lease_seconds=self._lease_seconds,
            event_types=list(self._consumers),
            max_attempts=self._max_attempts,
        )

        if event is None:
            return "idle"

        event_id = event["event_id"]
        consumer = self._consumers[event["event_type"]]

        try:
            consumer(event)
        except Exception as exc:
            self._repository.schedule_retry(
                event_id=event_id,
                claim_token=event["claim_token"],
                error=f"{type(exc).__name__}: {exc}",
                retry_delay_seconds=self._retry_delay_seconds,
                max_attempts=self._max_attempts,
            )
            return "retry_scheduled"

        # If this fails, leave recovery to the lease mechanism.
        # The consumer may run again, so it must be idempotent.
        self._repository.mark_delivered(
            event_id,
            claim_token=event["claim_token"],
        )

        return "delivered"