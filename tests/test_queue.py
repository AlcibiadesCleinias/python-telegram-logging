"""Test the queue handler."""

import logging
import queue
import threading
import time
from unittest.mock import patch

import pytest

from python_telegram_logging.handlers.async_ import AsyncTelegramHandler
from python_telegram_logging.handlers.sync import SyncTelegramHandler
from python_telegram_logging.queue import QueuedTelegramHandler
from python_telegram_logging.schemes import ParseMode


@pytest.fixture
def base_handler():
    handler = SyncTelegramHandler(token="test_token", chat_id="test_chat_id", parse_mode=ParseMode.HTML)
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


@pytest.fixture
def handler(base_handler):
    handler = QueuedTelegramHandler(base_handler, queue_size=1)  # Queue size of 1 for testing
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


def test_handler_initialization(handler, base_handler):
    assert handler.handler == base_handler
    assert isinstance(handler.queue, queue.Queue)
    assert isinstance(handler._worker, threading.Thread)
    assert handler._worker.daemon is True


def test_async_handler_rejected():
    """Test that async handler is rejected."""
    async_handler = AsyncTelegramHandler(token="test_token", chat_id="test_chat_id", parse_mode=ParseMode.HTML)
    with pytest.raises(ValueError) as exc_info:
        QueuedTelegramHandler(async_handler)
    assert "AsyncTelegramHandler already includes queue functionality" in str(exc_info.value)


def test_emit(handler):
    record = logging.LogRecord(
        name="test_logger", level=logging.INFO, pathname="test.py", lineno=1, msg="Test message", args=(), exc_info=None
    )

    with patch.object(handler.handler, "handle") as mock_handle:
        handler.emit(record)
        time.sleep(0.1)  # Give the worker thread time to process

        # Verify the record was processed
        mock_handle.assert_called_once_with(record)


def test_queue_full(handler):
    """Test that records are dropped when queue is full."""
    # Create events to control the test flow
    processing_started = threading.Event()  # Signals when worker starts processing
    can_continue = threading.Event()  # Controls when the worker can continue

    def blocking_handle(record):
        # Signal that we've started processing
        processing_started.set()
        # Wait until we're told to continue
        if not can_continue.wait(timeout=1.0):  # Add timeout to prevent hanging
            raise TimeoutError("Test timed out waiting for can_continue")

    with patch.object(handler.handler, "handle") as mock_handle:
        mock_handle.side_effect = blocking_handle

        # Fill the queue (queue size is 1)
        first_record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="First message",
            args=(),
            exc_info=None,
        )
        handler.emit(first_record)

        # Wait for the worker to start processing
        if not processing_started.wait(timeout=1.0):
            pytest.fail("Worker thread did not start processing within timeout")

        # At this point, the worker is processing the first record and the queue should be empty
        # Try to emit two more records to ensure one is dropped
        for i in range(2):
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg=f"Message {i+2}",
                args=(),
                exc_info=None,
            )
            with patch.object(handler, "handleError") as mock_handle_error:
                handler.emit(record)
                if i == 1:  # The second record should trigger handleError
                    assert mock_handle_error.called, "handleError should be called when queue is full"

        # Let the worker thread continue
        can_continue.set()


def test_close(handler):
    # First, verify the worker is running
    assert handler._worker.is_alive()

    # Close the handler
    handler.close()

    # Verify the worker has stopped
    assert not handler._worker.is_alive()

    # Try to put something in the queue after closing
    record = logging.LogRecord(
        name="test_logger", level=logging.INFO, pathname="test.py", lineno=1, msg="Test message", args=(), exc_info=None
    )
    handler.emit(record)  # Should be ignored when shutdown

    # Queue should be empty since we're shutdown
    assert handler.queue.empty()


def test_handler_cleanup(handler):
    """Test that underlying handler is closed properly."""
    with patch.object(handler.handler, "close") as mock_close:
        handler.close()
        mock_close.assert_called_once()
