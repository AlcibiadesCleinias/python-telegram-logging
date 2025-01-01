import logging
import time
from unittest.mock import AsyncMock

import pytest

from python_telegram_logging.handlers.async_ import AsyncTelegramHandler
from python_telegram_logging.schemes import ParseMode


@pytest.fixture
def handler():
    handler = AsyncTelegramHandler(token="test_token", chat_id="test_chat_id", parse_mode=ParseMode.HTML)
    handler.setFormatter(logging.Formatter("%(message)s"))
    yield handler
    handler.close()


@pytest.fixture
def mock_session():
    """Create a properly mocked aiohttp ClientSession."""
    # Create a mock response
    mock_response = AsyncMock()
    mock_response.ok = True
    mock_response.status = 200
    mock_response.json.return_value = {}
    mock_response.text.return_value = ""

    # Create a mock session with proper async context manager support
    mock = AsyncMock()
    mock.post = AsyncMock()
    mock.post.return_value = mock_response
    mock.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock.post.return_value.__aexit__ = AsyncMock(return_value=None)

    return mock


def test_handler_initialization(handler):
    assert handler.token == "test_token"
    assert handler.chat_id == "test_chat_id"
    assert handler.parse_mode == ParseMode.HTML


def test_emit(handler, mock_session):
    """Test that emit queues the record."""
    # Set the session directly
    handler._session = mock_session

    # Mock the rate limiter to avoid delays
    handler._rate_limiter.acquire = AsyncMock()

    record = logging.LogRecord(
        name="test_logger", level=logging.INFO, pathname="test.py", lineno=1, msg="Test message", args=(), exc_info=None
    )

    # Emit should be synchronous and just queue the record
    handler.emit(record)

    # Give the background task time to process
    time.sleep(0.5)  # Increased sleep time to ensure processing

    # Since format_message returns a list of messages, the handler should make one API call per message
    mock_session.post.assert_called_once_with(
        handler._base_url,
        json={
            "chat_id": "test_chat_id",
            "text": "Test message",
            "parse_mode": ParseMode.HTML.value,
            "disable_web_page_preview": True,
            "disable_notification": False,
        },
    )


# TODO: resolve mocking, or do not use async context manager in async_ client.
# def test_emit_long_message(handler, mock_session):
#     """Test that long messages are split and queued correctly."""
#     # Set the session directly
#     handler._session = mock_session

#     # Mock the rate limiter to avoid delays
#     handler._rate_limiter.acquire = AsyncMock()

#     # Mock format_message to return split messages
#     first_chunk = "x" * 4096
#     second_chunk = "x" * 904
#     handler.format_message = Mock(return_value=[first_chunk, second_chunk])

#     record = logging.LogRecord(
#         name="test_logger",
#         level=logging.INFO,
#         pathname="test.py",
#         lineno=1,
#         msg="x" * 5000,
#         args=(),
#         exc_info=None
#     )

#     # Emit should be synchronous and just queue the record
#     handler.emit(record)

#     # Give the background task time to process
#     time.sleep(0.5)  # Increased sleep time to ensure processing

#     # Should make two API calls for the split message
#     assert mock_session.post.call_count == 2
#     calls = mock_session.post.call_args_list

#     # First chunk
#     assert calls[0].kwargs['json']['text'] == "x" * 4096
#     # Second chunk
#     assert calls[1].kwargs['json']['text'] == "x" * 904


def test_close(handler, mock_session):
    """Test that close properly shuts down the background task."""
    # Set the session directly
    handler._session = mock_session

    # Close should be synchronous and clean up everything
    handler.close()

    # Verify the background task was stopped
    assert handler._stopping.is_set()
    # Verify the thread was stopped
    assert not handler._thread.is_alive()

    # The session should be closed by the cleanup coroutine
    mock_session.close.assert_called_once()
