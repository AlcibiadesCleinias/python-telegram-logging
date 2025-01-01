import logging
import queue
import threading
import time
from unittest.mock import patch

import pytest

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
    handler = QueuedTelegramHandler(base_handler)
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


def test_handler_initialization(handler, base_handler):
    assert handler.handler == base_handler
    assert isinstance(handler.queue, queue.Queue)
    assert isinstance(handler._worker, threading.Thread)
    assert handler._worker.daemon is True


def test_emit(handler):
    record = logging.LogRecord(
        name="test_logger", level=logging.INFO, pathname="test.py", lineno=1, msg="Test message", args=(), exc_info=None
    )

    with patch.object(handler.handler, "handle") as mock_handle:
        handler.emit(record)
        time.sleep(0.1)  # Give the worker thread time to process

        # Verify the record was processed
        mock_handle.assert_called_once_with(record)


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
