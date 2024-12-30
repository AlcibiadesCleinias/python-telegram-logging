import asyncio
import logging
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from python_telegram_logging.handlers.async_ import AsyncTelegramHandler
from python_telegram_logging.handlers.sync import SyncTelegramHandler
from python_telegram_logging.schemes import ParseMode


@pytest.fixture
def mock_session():
    """Create a properly mocked aiohttp ClientSession."""
    mock_response = AsyncMock()
    mock_response.ok = True
    mock_response.status = 200
    mock_response.json.return_value = {}
    mock_response.text.return_value = ""

    mock = AsyncMock()
    mock.post = AsyncMock()
    mock.post.return_value = mock_response

    return mock


@pytest.fixture
def mock_requests():
    """Create a properly mocked requests response."""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_response.text = ""

    return mock_response


async def async_main(logger: logging.Logger):
    """Simulate an async application using the logger."""
    logger.info("Starting async task")
    await asyncio.sleep(0.1)  # Simulate some async work
    logger.info("Async task completed")


def sync_main(logger: logging.Logger):
    """Simulate a sync application using the logger."""
    logger.info("Starting sync task")
    time.sleep(0.1)  # Simulate some work
    logger.info("Sync task completed")


@pytest.mark.asyncio
async def test_async_logger_integration(mock_session):
    """Test that the async logger works in an async application."""
    # Set up the logger
    logger = logging.getLogger("async_test")
    logger.setLevel(logging.INFO)

    # Create and configure the handler
    handler = AsyncTelegramHandler(token="test_token", chat_id="test_chat_id", parse_mode=ParseMode.HTML)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler._session = mock_session  # Inject our mock session
    handler._rate_limiter.acquire = AsyncMock()  # Avoid rate limiting in tests
    logger.addHandler(handler)

    try:
        # Run our async application
        await async_main(logger)

        # Give the background task time to process
        await asyncio.sleep(0.5)

        # Verify that both messages were sent
        assert mock_session.post.call_count == 2
        calls = mock_session.post.call_args_list

        # Check the messages
        assert calls[0].kwargs["json"]["text"] == "Starting async task"
        assert calls[1].kwargs["json"]["text"] == "Async task completed"
    finally:
        # Clean up
        handler.close()
        logger.removeHandler(handler)


def test_sync_logger_integration(mock_requests):
    """Test that the sync logger works in a synchronous application."""
    # Set up the logger
    logger = logging.getLogger("sync_test")
    logger.setLevel(logging.INFO)

    # Create and configure the handler
    handler = SyncTelegramHandler(token="test_token", chat_id="test_chat_id", parse_mode=ParseMode.HTML)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    # Mock requests.post to return our mock response
    with patch("requests.post", return_value=mock_requests) as mock_post:
        try:
            # Run our sync application
            sync_main(logger)

            # Verify that both messages were sent
            assert mock_post.call_count == 2
            calls = mock_post.call_args_list

            # Check the messages
            assert calls[0].kwargs["json"]["text"] == "Starting sync task"
            assert calls[1].kwargs["json"]["text"] == "Sync task completed"
        finally:
            # Clean up
            handler.close()
            logger.removeHandler(handler)
