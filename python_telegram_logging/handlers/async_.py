"""Asynchronous Telegram logging handler implementation."""

import asyncio
import logging
import threading
import time
from typing import Any, Optional, Union

import aiohttp

from ..exceptions import RateLimitError, TelegramAPIError
from ..rate_limiting import BaseRateLimiter, TimeProvider
from .base_queue import BaseQueueHandler
from .base_telegram import BaseTelegramHandler


class AsyncTimeProvider(TimeProvider):
    """Asynchronous time provider using event loop time."""

    def get_time(self) -> float:
        """Get current time in seconds."""
        return asyncio.get_event_loop().time()


class AsyncRateLimiter(BaseRateLimiter):
    """Rate limiter for asynchronous operations."""

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        super().__init__(AsyncTimeProvider())
        self._lock = asyncio.Lock()

    def _acquire_lock(self) -> asyncio.Lock:
        return self._lock

    def _release_lock(self, lock: asyncio.Lock) -> None:
        lock.release()

    async def _sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)

    async def _check_limits(self, chat_id: Union[str, int]) -> None:
        """Check and enforce rate limits for a chat.

        Args:
            chat_id: The chat ID to check

        Raises:
            RateLimitError: If rate limits would be exceeded
        """
        current_time = self._time_provider.get_time()
        state = self._chat_states[chat_id]

        # Clean up old messages
        state.clean_old_messages(current_time)

        # Check if we would exceed limits
        would_exceed, wait_time = state.would_exceed_rate_limit(current_time)
        if would_exceed:
            await self._sleep(wait_time)
            current_time = self._time_provider.get_time()

        # Record the message
        state.record_message(current_time)

    async def acquire(self, chat_id: Union[str, int]) -> None:
        """Acquire permission to send a message.

        This is an async version of the base class's acquire method.
        """
        async with self._lock:
            await self._check_limits(chat_id)


class AsyncTelegramHandler(BaseTelegramHandler, BaseQueueHandler):
    """Asynchronous Telegram logging handler.

    This handler uses a queue to buffer messages and processes them
    asynchronously in a background task. This ensures compatibility with
    the synchronous logging framework while still allowing async HTTP calls.
    """

    def __init__(self, *args, queue_size: int = 1000, **kwargs):
        """Initialize the handler."""
        BaseTelegramHandler.__init__(self, *args, **kwargs)
        BaseQueueHandler.__init__(self, queue_size=queue_size, level=kwargs.get("level", logging.NOTSET))
        self._session: Optional[aiohttp.ClientSession] = None
        self._task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

        # Start the background processing
        self._start_background_processing()

    def _create_rate_limiter(self) -> Any:
        return AsyncRateLimiter()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record."""
        return BaseQueueHandler.emit(self, record)

    def _start_background_processing(self) -> None:
        """Start the background processing thread and async task."""

        def run_event_loop():
            try:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                self._task = self._loop.create_task(self._process_queue())
                self._loop.run_forever()
            except Exception:
                self.handleError(None)  # type: ignore
            finally:
                try:
                    if self._loop is not None:
                        # Cancel all tasks
                        for task in asyncio.all_tasks(self._loop):
                            task.cancel()
                        # Run the event loop once more to let tasks clean up
                        self._loop.run_until_complete(asyncio.sleep(0))
                        self._loop.close()
                except Exception:
                    pass

        self._thread = threading.Thread(target=run_event_loop, daemon=True)
        self._thread.start()

    async def _process_queue(self) -> None:
        """Process records from the queue."""
        while not self._shutdown.is_set() or not self.queue.empty():
            try:
                record = self.queue.get_nowait()
            except:  # Queue.Empty and others  # noqa: E722
                if self._shutdown.is_set():
                    break
                await asyncio.sleep(0.1)
                continue

            try:
                await self._async_emit(record)
            except Exception:
                self.handleError(record)  # type: ignore
            finally:
                self.queue.task_done()

    async def _async_emit(self, record: logging.LogRecord) -> None:
        """Actually emit the record asynchronously."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        messages = self.format_message(record)
        for message in messages:
            payload = self.prepare_payload(message)

            await self._rate_limiter.acquire(self.chat_id)
            try:
                async with self._session.post(self._base_url, json=payload) as response:
                    if response.status == 429:  # Too Many Requests
                        error_data = await response.json()
                        retry_after = error_data.get("retry_after", 1)
                        raise RateLimitError(retry_after)

                    if not response.ok:
                        error_text = await response.text()
                        raise TelegramAPIError(status_code=response.status, response_text=error_text)
            except Exception as e:
                if not isinstance(e, asyncio.CancelledError):
                    raise

    def close(self) -> None:
        """Close the handler and clean up resources synchronously."""
        if not self._shutdown.is_set():
            self._shutdown.set()

            # Wait for the queue to be empty
            timeout = 5  # seconds
            start_time = time.time()
            while not self.queue.empty() and time.time() - start_time < timeout:
                time.sleep(0.1)

            if self._loop is not None:
                try:
                    # Cancel the task and clean up
                    if self._task is not None:
                        self._loop.call_soon_threadsafe(self._task.cancel)
                    future = asyncio.run_coroutine_threadsafe(self._cleanup(), self._loop)
                    future.result(timeout=5)  # Wait up to 5 seconds
                except:  # TimeoutError and others  # noqa: E722
                    pass

                # Stop the event loop
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
