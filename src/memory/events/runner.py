import logging
import threading

from src.memory.events.worker import EventOutboxWorker

logger = logging.getLogger(__name__)


class EventOutboxRunner:
    """Run the outbox worker periodically in a background thread."""

    def __init__(
        self,
        worker: EventOutboxWorker | None = None,
        *,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")

        self._worker = worker or EventOutboxWorker()
        self._poll_interval = poll_interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="soul-event-outbox",
            daemon=False,
        )
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=timeout)

            if self._thread.is_alive():
                raise TimeoutError(
                    "Outbox runner did not stop within the timeout"
                )

            self._thread = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                result = self._worker.run_once()

                if result == "idle":
                    self._stop_event.wait(self._poll_interval)

            except Exception:
                logger.exception("Outbox worker iteration failed")
                self._stop_event.wait(self._poll_interval)
