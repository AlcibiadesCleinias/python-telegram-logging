"""Asynchronous Telegram logging handler implementation."""

import asyncio
import logging
import threading
import time
from queue import SimpleQueue
from typing import Any, Optional

import aiohttp

from ..exceptions import TelegramAPIError
from .base import BaseTelegramHandler


class AsyncRateLimiter:
    """Rate limiter for asynchronous operations."""

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        self._lock = asyncio.Lock()
        self._last_request_time = 0.0

    async def acquire(self) -> None:
        """Acquire permission to send a message."""
        async with self._lock:
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time

            if time_since_last < 1.0:
                await asyncio.sleep(1.0 - time_since_last)

            self._last_request_time = asyncio.get_event_loop().time()


class AsyncTelegramHandler(BaseTelegramHandler):
    """Asynchronous Telegram logging handler.

    This handler uses a queue to buffer messages and processes them
    asynchronously in a background task. This ensures compatibility with
    the synchronous logging framework while still allowing async HTTP calls.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the handler."""
        super().__init__(*args, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None
        self._queue: SimpleQueue = SimpleQueue()
        self._task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stopping = threading.Event()

        # Start the background processing
        self._start_background_processing()

    def _create_rate_limiter(self) -> Any:
        return AsyncRateLimiter()

    def _start_background_processing(self) -> None:
        """Start the background processing thread and async task."""

        def run_event_loop():
            try:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                self._task = self._loop.create_task(self._process_queue())
                self._loop.run_forever()
            except Exception:
                # Log any errors that occur in the background thread
                self.handleError(None)  # type: ignore
            finally:
                # Clean up the event loop
                if self._loop is not None and self._loop.is_running():
                    self._loop.stop()
                if self._loop is not None and not self._loop.is_closed():
                    self._loop.close()

        self._thread = threading.Thread(target=run_event_loop, daemon=True)
        self._thread.start()

    async def _process_queue(self) -> None:
        """Process records from the queue."""
        while not self._stopping.is_set() or not self._queue.empty():
            try:
                record = self._queue.get_nowait()
            except:  # Queue.Empty and others  # noqa: E722
                if self._stopping.is_set():
                    break
                await asyncio.sleep(0.1)
                continue

            try:
                await self._async_emit(record)
            except Exception:
                self.handleError(record)  # type: ignore

    async def _async_emit(self, record: logging.LogRecord) -> None:
        """Actually emit the record asynchronously."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        messages = self.format_message(record)
        for message in messages:
            payload = self.prepare_payload(message)

            await self._rate_limiter.acquire()
            async with self._session.post(self._base_url, json=payload) as response:
                if not response.ok:
                    error_text = await response.text()
                    raise TelegramAPIError(f"Telegram API returned {response.status}: {error_text}")

    def emit(self, record: logging.LogRecord) -> None:
        """Queue the record for async processing.

        This method is called by the logging framework and must be synchronous.
        The actual sending happens in the background task.
        """
        try:
            self._queue.put_nowait(record)
        except Exception:
            self.handleError(record)  # type: ignore

    def close(self) -> None:
        """Close the handler and clean up resources synchronously."""
        if not self._stopping.is_set():
            self._stopping.set()

            # Wait for the queue to be empty
            timeout = 5  # seconds
            start_time = time.time()
            while not self._queue.empty() and time.time() - start_time < timeout:
                time.sleep(0.1)

            if self._loop is not None:
                if self._task is not None:
                    # Schedule task cancellation in the event loop
                    future = asyncio.run_coroutine_threadsafe(self._cleanup(), self._loop)
                    try:
                        future.result(timeout=5)  # Wait up to 5 seconds
                    except:  # TimeoutError and others  # noqa: E722
                        pass

                # Stop the event loop
                if not self._loop.is_closed():
                    self._loop.call_soon_threadsafe(self._loop.stop)

            # Wait for the thread to finish
            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=5)

            super().close()

    async def _cleanup(self) -> None:
        """Clean up async resources."""
        if self._session is not None:
            await self._session.close()
            self._session = None
