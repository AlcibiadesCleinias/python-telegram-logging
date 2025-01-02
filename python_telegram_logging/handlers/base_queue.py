"""Base queue handler for both sync and async implementations."""

import logging
import queue
import threading
from abc import ABC, abstractmethod


class BaseQueueHandler(logging.Handler, ABC):
    """Base class for queue-based handlers.

    This class provides the core queue functionality that can be used by both
    sync and async implementations.
    """

    def __init__(
        self,
        queue_size: int = 1000,
        level: int = logging.NOTSET,
    ) -> None:
        """Initialize the handler.

        Args:
            queue_size: Maximum number of records in the queue
            level: Minimum logging level
        """
        super().__init__(level)
        self.queue = queue.Queue(maxsize=queue_size)
        self._shutdown = threading.Event()

    def emit(self, record: logging.LogRecord) -> None:
        """Put the record into the queue.

        If the queue is full, the record will be dropped and handleError will be called.
        If the handler is shutting down, the record will be dropped silently.
        """
        if self._shutdown.is_set():
            return

        try:
            self.queue.put_nowait(record)
        except queue.Full:
            self.handleError(record)

    @abstractmethod
    def _process_queue(self) -> None:
        """Process records from the queue.

        This method should be implemented by subclasses to define how
        records are processed from the queue.
        """

    def close(self) -> None:
        """Stop processing and clean up resources."""
        self._shutdown.set()
        super().close()
