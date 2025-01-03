"""Python Telegram Logging."""
from importlib.metadata import version

from .handlers.async_ import AsyncTelegramHandler
from .handlers.base_telegram import BaseTelegramHandler
from .handlers.queue import QueuedTelegramHandler
from .handlers.sync import SyncTelegramHandler
from .schemes import ParseMode, RetryStrategy

__all__ = [
    "AsyncTelegramHandler",
    "BaseTelegramHandler",
    "QueuedTelegramHandler",
    "SyncTelegramHandler",
    "ParseMode",
    "RetryStrategy",
]

# Get version from package metadata (which gets it from git tags via hatch-vcs)
try:
    __version__ = version("python-telegram-logging")
except Exception:  # pragma: no cover
    # package is not installed
    __version__ = "unknown"
