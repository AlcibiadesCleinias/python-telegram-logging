"""Base classes and interfaces for Telegram logging handlers."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

from ..schemes import ParseMode, RetryStrategy

TELEGRAM_MESSAGE_LIMIT = 4096


class BaseTelegramHandler(logging.Handler, ABC):
    """Base class for Telegram logging handlers.

    This handler implements Telegram's rate limiting rules:
    - In a single chat: Maximum 1 message per second
    - In groups: Maximum 20 messages per minute

    Rate limiting is handled automatically by the handler. If a rate limit
    is exceeded, the handler will wait the appropriate amount of time before
    sending the next message.

    For group chats, messages are limited to 20 per minute across all bots
    in the group. The handler will automatically wait if this limit is reached.
    """

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
            parse_mode: Message parsing mode (default: HTML)
            disable_web_page_preview: Whether to disable web page previews (default: True)
            disable_notification: Whether to disable notifications (default: False)
            retry_strategy: Strategy for handling rate limits (default: EXPONENTIAL_BACKOFF)
            error_callback: Optional callback for handling errors
            level: Minimum logging level (default: NOTSET)

        TODO: add implementation for retry_strategy.
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
        """Create and return a rate limiter instance.

        This method should be implemented by subclasses to return either
        a SyncRateLimiter or AsyncRateLimiter instance.
        """

    @abstractmethod
    def emit(self, record: logging.LogRecord) -> None:
        """Send the log record to Telegram.

        This method should handle:
        1. Formatting the message
        2. Splitting long messages if needed
        3. Rate limiting
        4. Making the actual API calls
        5. Error handling

        Subclasses must implement this method.
        """

    def format_message(self, record: logging.LogRecord) -> List[str]:
        """Format the log record into a list of Telegram messages.

        If the message is longer than Telegram's limit (TELEGRAM_MESSAGE_LIMIT characters),
        it will be split into multiple messages.

        Args:
            record: The log record to format

        Returns:
            List of message strings, each under TELEGRAM_MESSAGE_LIMIT characters
        """
        message = self.format(record)
        return [message[i : i + TELEGRAM_MESSAGE_LIMIT] for i in range(0, len(message), TELEGRAM_MESSAGE_LIMIT)]

    def prepare_payload(self, message: str) -> Dict[str, Any]:
        """Prepare the payload for the Telegram API request.

        Args:
            message: The message text to send

        Returns:
            Dictionary containing the API request payload
        """
        return {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": self.parse_mode.value,
            "disable_web_page_preview": self.disable_web_page_preview,
            "disable_notification": self.disable_notification,
        }

    def handle_error(self, error: Exception) -> None:
        """Handle any errors that occur while sending messages.

        If an error_callback was provided, it will be called with the error.
        Any exceptions in the callback are silently ignored.

        Args:
            error: The exception that occurred
        """
        if self.error_callback:
            try:
                self.error_callback(error)
            except Exception:
                pass
