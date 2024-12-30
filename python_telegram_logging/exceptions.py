"""Handler exceptions."""


class TelegramLogError(Exception):
    """Base exception for Telegram logging errors."""


class RateLimitError(TelegramLogError):
    """Raised when hitting Telegram's rate limits."""

    def __init__(self, retry_after: float):
        """Initialize the RateLimitError exception."""
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")


class TelegramAPIError(TelegramLogError):
    """Raised when Telegram API returns an error."""

    def __init__(self, status_code: int, response_text: str):
        """Initialize the TelegramAPIError exception."""
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(f"Telegram API error {status_code}: {response_text}")
