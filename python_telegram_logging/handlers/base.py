"""Base classes and interfaces for Telegram logging handlers."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Union

from ..schemes import ParseMode, RetryStrategy


class BaseTelegramHandler(logging.Handler, ABC):
    """Base class for Telegram logging handlers."""

    def __init__(
        self,
        token: str,
        chat_id: Union[str, int],
        parse_mode: ParseMode = ParseMode.HTML,
        disable_web_page_preview: bool = True,
        disable_notification: bool = False,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        error_callback: Optional[Callable[[Exception], None]] = None,
        level: int = logging.NOTSET,
    ) -> None:
        """Initialize the handler.

        Args:
            token: Telegram bot token
            chat_id: Target chat ID
            parse_mode: Message parsing mode
            disable_web_page_preview: Whether to disable web page previews
            disable_notification: Whether to disable notifications
            retry_strategy: Strategy for handling rate limits
            error_callback: Optional callback for handling errors
            level: Minimum logging level
        TODO: implement retry_strategy
        """
        super().__init__(level)
        self.token = token
        self.chat_id = chat_id
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview
        self.disable_notification = disable_notification
        self.retry_strategy = retry_strategy
        self.error_callback = error_callback

        self._base_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._rate_limiter = self._create_rate_limiter()

    @abstractmethod
    def _create_rate_limiter(self) -> Any:
        """Create and return a rate limiter instance."""

    @abstractmethod
    def emit(self, record: logging.LogRecord) -> None:
        """Send the log record to Telegram."""

    def format_message(self, record: logging.LogRecord) -> list[str]:
        """Format the log record into a list of Telegram messages.

        If the message is longer than Telegram's limit (4096 characters),
        it will be split into multiple messages.
        """
        message = self.format(record)
        return [message[i : i + 4096] for i in range(0, len(message), 4096)]

    def prepare_payload(self, message: str) -> Dict[str, Any]:
        """Prepare the payload for the Telegram API request."""
        return {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": self.parse_mode.value,
            "disable_web_page_preview": self.disable_web_page_preview,
            "disable_notification": self.disable_notification,
        }

    def handle_error(self, error: Exception) -> None:
        """Handle any errors that occur while sending messages."""
        if self.error_callback:
            try:
                self.error_callback(error)
            except Exception:
                pass
