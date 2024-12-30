"""Queue-based handler for asynchronous logging to Telegram."""

import logging
import queue
import threading

from .handlers.base import BaseTelegramHandler


class QueuedTelegramHandler(logging.Handler):
    """A handler that queues log records and sends them to Telegram in a separate thread."""

    def __init__(
        self,
        handler: BaseTelegramHandler,
        queue_size: int = 1000,
        level: int = logging.NOTSET,
    ) -> None:
        """Initialize the handler.

        Args:
            handler: The underlying Telegram handler
            queue_size: Maximum number of records in the queue
            level: Minimum logging level
        """
        super().__init__(level)
        self.handler = handler
        self.queue = queue.Queue(maxsize=queue_size)
        self._shutdown = threading.Event()
        self._worker = threading.Thread(target=self._process_queue, daemon=True)
        self._worker.start()

    def emit(self, record: logging.LogRecord) -> None:
        """Put the record into the queue."""
        if self._shutdown.is_set():
            return

        try:
            self.queue.put(record)
        except queue.Full:
            self.handleError(record)

    def _process_queue(self) -> None:
        """Process records from the queue."""
        while not self._shutdown.is_set() or not self.queue.empty():
            try:
                record = self.queue.get(timeout=0.1)
                try:
                    self.handler.handle(record)
                except Exception:
                    self.handleError(record)
                finally:
                    self.queue.task_done()
            except queue.Empty:
                continue

    def close(self) -> None:
        """Stop the worker thread and close the queue."""
        self._shutdown.set()
        if self._worker.is_alive():
            self._worker.join()
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                break
        self.queue.join()
        super().close()
