
from collections.abc import Callable
from threading import RLock

from src.memory.events.repository import MemoryEventRepository
from src.memory.events.schemas import MemoryEvent, MemoryEventType


EventHandler = Callable[[MemoryEvent], None]


class MemoryEventPublisher:
    def __init__(
        self,
        repository: MemoryEventRepository | None = None,
    ) -> None:
        self._handlers: dict[MemoryEventType, list[EventHandler]] = {}
        self._lock = RLock()
        self._repository = repository or MemoryEventRepository()

    def subscribe(
        self,
        event_type: MemoryEventType,
        handler: EventHandler,
    ) -> None:
        with self._lock:
            handlers = self._handlers.setdefault(event_type, [])
            if handler not in handlers:
                handlers.append(handler)

    def unsubscribe(
        self,
        event_type: MemoryEventType,
        handler: EventHandler,
    ) -> bool:
        with self._lock:
            handlers = self._handlers.get(event_type)

            if not handlers or handler not in handlers:
                return False

            handlers.remove(handler)

            if not handlers:
                del self._handlers[event_type]

            return True

    def persist(
        self,
        event: MemoryEvent,
        *,
        connection=None,
    ) -> bool:
        """Persist an event, optionally inside a caller's transaction."""
        return self._repository.save(event, connection=connection)

    def notify(self, event: MemoryEvent) -> int:
        """Notify in-memory handlers without persisting the event again."""
        with self._lock:
            handlers = tuple(self._handlers.get(event.event_type, ()))

        successful_deliveries = 0

        for handler in handlers:
            handler(event)
            successful_deliveries += 1

        return successful_deliveries

    def publish(self, event: MemoryEvent) -> int:
        """Persist first, then notify handlers."""
        self.persist(event)
        return self.notify(event)

    def subscriber_count(
        self,
        event_type: MemoryEventType,
    ) -> int:
        with self._lock:
            return len(self._handlers.get(event_type, ()))
