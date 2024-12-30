"""Synchronous Telegram logging handler."""
import logging
import time
from threading import Lock
from typing import Any

import requests

from ..exceptions import RateLimitError, TelegramAPIError
from .base import BaseTelegramHandler


class SyncRateLimiter:
    """Thread-safe rate limiter for synchronous operations."""

    def __init__(self):
        """Initialize the rate limiter."""
        self._lock = Lock()
        self._last_request_time = 0.0

    def acquire(self) -> None:
        """Acquire permission to send a message."""
        with self._lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time

            if time_since_last < 1.0:
                time.sleep(1.0 - time_since_last)

            self._last_request_time = time.time()


class SyncTelegramHandler(BaseTelegramHandler):
    """Synchronous Telegram logging handler."""

    def _create_rate_limiter(self) -> Any:
        return SyncRateLimiter()

    def emit(self, record: logging.LogRecord) -> None:
        """Send the log record to Telegram."""
        try:
            messages = self.format_message(record)

            for message in messages:
                self._rate_limiter.acquire()
                payload = self.prepare_payload(message)

                response = requests.post(self._base_url, json=payload)

                if response.status_code == 429:
                    retry_after = response.json().get("retry_after", 1)
                    raise RateLimitError(retry_after)

                if not response.ok:
                    raise TelegramAPIError(response.status_code, response.text)

        except Exception as e:
            self.handle_error(e)
