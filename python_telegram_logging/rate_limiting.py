"""Rate limiting functionality for Telegram handlers.

This module implements Telegram's rate limiting rules:
- Per chat: Maximum 1 message per second
- In groups: Maximum 20 messages per minute
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Protocol, TypeVar, Union


@dataclass
class ChatState:
    """State for a single chat's rate limiting."""

    last_message_time: float = 0.0
    message_timestamps: List[float] = field(default_factory=list)

    def clean_old_messages(self, current_time: float, window: float = 60.0) -> None:
        """Remove messages older than the window.

        Args:
            current_time: Current timestamp
            window: Time window in seconds (default: 60s for minute window)
        """
        cutoff = current_time - window
        self.message_timestamps = [ts for ts in self.message_timestamps if ts > cutoff]

    def would_exceed_rate_limit(self, current_time: float) -> tuple[bool, float]:
        """Check if sending a message now would exceed rate limits.

        Args:
            current_time: Current timestamp

        Returns:
            Tuple of (would_exceed, wait_time)
        """
        # Check per-second limit
        time_since_last = current_time - self.last_message_time
        if time_since_last < 1.0:
            return True, 1.0 - time_since_last

        # Check per-minute limit (20 messages)
        if len(self.message_timestamps) >= 20:
            wait_time = self.message_timestamps[0] + 60 - current_time
            if wait_time > 0:
                return True, wait_time

        return False, 0.0

    def record_message(self, current_time: float) -> None:
        """Record that a message was sent.

        Args:
            current_time: Current timestamp
        """
        self.last_message_time = current_time
        self.message_timestamps.append(current_time)


class TimeProvider(Protocol):
    """Protocol for getting current time."""

    def get_time(self) -> float:
        """Get current time in seconds."""
        ...


T = TypeVar("T")  # Type variable for the lock type


class BaseRateLimiter(ABC):
    """Base class for rate limiters.

    This provides the core rate limiting logic, while leaving
    synchronization details to the concrete implementations.
    """

    def __init__(self, time_provider: TimeProvider) -> None:
        """Initialize the rate limiter.

        Args:
            time_provider: Object that provides current time
        """
        self._time_provider = time_provider
        self._chat_states: Dict[Union[str, int], ChatState] = defaultdict(ChatState)

    @abstractmethod
    def _acquire_lock(self) -> T:
        """Acquire the synchronization lock."""

    @abstractmethod
    def _release_lock(self, lock: T) -> None:
        """Release the synchronization lock."""

    @abstractmethod
    def _sleep(self, seconds: float) -> None:
        """Sleep for the specified duration."""

    def _check_limits(self, chat_id: Union[str, int]) -> None:
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
            self._sleep(wait_time)
            current_time = self._time_provider.get_time()

        # Record the message
        state.record_message(current_time)

    def acquire(self, chat_id: Union[str, int]) -> None:
        """Acquire permission to send a message.

        This method is thread-safe/coroutine-safe depending on the implementation.

        Args:
            chat_id: The target chat ID

        Raises:
            RateLimitError: If rate limits would be exceeded
        """
        lock = self._acquire_lock()
        try:
            self._check_limits(chat_id)
        finally:
            self._release_lock(lock)
