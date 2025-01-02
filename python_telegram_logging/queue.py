"""Queue-based handler for synchronous logging to Telegram."""

import logging
import threading
from typing import Optional

from .handlers.async_ import AsyncTelegramHandler
from .handlers.base import BaseTelegramHandler
from .handlers.base_queue import BaseQueueHandler


class QueuedTelegramHandler(BaseQueueHandler):
    """A handler that queues log records and sends them to Telegram in a separate thread.

    This handler is designed to work with synchronous handlers only. For asynchronous
    handlers, use AsyncTelegramHandler directly as it already includes queue functionality.
    """

    def __init__(
        self,
        handler: BaseTelegramHandler,
        queue_size: int = 1000,
        level: int = logging.NOTSET,
    ) -> None:
        """Initialize the handler.

        Args:
            handler: The underlying Telegram handler (must be synchronous)
            queue_size: Maximum number of records in the queue
            level: Minimum logging level

        Raises:
            ValueError: If an async handler is provided
        """
        if isinstance(handler, AsyncTelegramHandler):
            raise ValueError(
                "AsyncTelegramHandler already includes queue functionality. "
                "Use it directly instead of wrapping it in QueuedTelegramHandler."
            )

        super().__init__(queue_size=queue_size, level=level)
        self.handler = handler
        self._worker: Optional[threading.Thread] = None
        self._start_worker()

    def _start_worker(self) -> None:
        """Start the worker thread."""
        self._worker = threading.Thread(target=self._process_queue, daemon=True)
        self._worker.start()

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
            except:  # Queue.Empty and others  # noqa: E722
                continue

    def close(self) -> None:
        """Stop the worker thread and close the queue."""
        super().close()
        if self._worker is not None and self._worker.is_alive():
            self._worker.join(timeout=5)
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except:  # Queue.Empty and others  # noqa: E722
                break
        self.queue.join()
        self.handler.close()
