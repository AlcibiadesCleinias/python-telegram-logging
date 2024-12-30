"""Schema for Telegram API."""
from dataclasses import dataclass
from enum import Enum, auto


class ParseMode(str, Enum):
    """Telegram message parse mode options."""

    HTML = "HTML"
    MARKDOWN = "MARKDOWN"
    MARKDOWN_V2 = "MarkdownV2"


class RetryStrategy(Enum):
    """Strategy for handling rate limiting and retries."""

    EXPONENTIAL_BACKOFF = auto()
    LINEAR_BACKOFF = auto()
    DROP = auto()


@dataclass
class TelegramMessage:
    """Schema for a Telegram message."""

    chat_id: str | int
    text: str
    parse_mode: ParseMode
    disable_web_page_preview: bool = True
    disable_notification: bool = False

    def to_dict(self) -> dict:
        """Convert the message to a dictionary for the Telegram API."""
        result = {
            "chat_id": self.chat_id,
            "text": self.text,
            "parse_mode": self.parse_mode.value,
            "disable_web_page_preview": self.disable_web_page_preview,
            "disable_notification": self.disable_notification,
        }
        return result
