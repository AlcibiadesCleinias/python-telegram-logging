"""Synchronous Telegram logging handler."""

import logging
import time
from threading import Lock
from typing import Any

import requests

from ..exceptions import RateLimitError, TelegramAPIError
from ..rate_limiting import BaseRateLimiter, TimeProvider
from .base import BaseTelegramHandler


class SyncTimeProvider(TimeProvider):
    """Synchronous time provider using time.time()."""

    def get_time(self) -> float:
        """Get current time in seconds."""
        return time.time()


class SyncRateLimiter(BaseRateLimiter):
    """Thread-safe rate limiter for synchronous operations."""

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        super().__init__(SyncTimeProvider())
        self._lock = Lock()

    def _acquire_lock(self) -> Lock:
        self._lock.acquire()
        return self._lock

    def _release_lock(self, lock: Lock) -> None:
        lock.release()

    def _sleep(self, seconds: float) -> None:
        time.sleep(seconds)


class SyncTelegramHandler(BaseTelegramHandler):
    """Synchronous Telegram logging handler."""

    def _create_rate_limiter(self) -> Any:
        return SyncRateLimiter()

    def emit(self, record: logging.LogRecord) -> None:
        """Send the log record to Telegram."""
        try:
            messages = self.format_message(record)

            for message in messages:
                payload = self.prepare_payload(message)
                self._rate_limiter.acquire(self.chat_id)

                response = requests.post(self._base_url, json=payload)

                if response.status_code == 429:
                    retry_after = response.json().get("retry_after", 1)
                    raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds.")

                if not response.ok:
                    raise TelegramAPIError(f"Telegram API returned {response.status_code}: {response.text}")

        except Exception as e:
            self.handle_error(e)
