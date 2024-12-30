import logging
from unittest.mock import Mock, patch

import pytest

from python_telegram_logging.handlers.sync import SyncTelegramHandler
from python_telegram_logging.schemes import ParseMode


@pytest.fixture
def handler():
    handler = SyncTelegramHandler(token="test_token", chat_id="test_chat_id", parse_mode=ParseMode.HTML)
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


def test_handler_initialization(handler):
    assert handler.token == "test_token"
    assert handler.chat_id == "test_chat_id"
    assert handler.parse_mode == ParseMode.HTML


def test_emit(handler):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200

    with patch("python_telegram_logging.handlers.sync.requests.post", return_value=mock_response) as mock_post:
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        handler.emit(record)

        # Since format_message returns a list of messages, the handler should make one API call per message
        mock_post.assert_called_once_with(
            handler._base_url,
            json={
                "chat_id": "test_chat_id",
                "text": "Test message",
                "parse_mode": ParseMode.HTML.value,
                "disable_web_page_preview": True,
                "disable_notification": False,
            },
        )


def test_emit_long_message(handler):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200

    with patch("python_telegram_logging.handlers.sync.requests.post", return_value=mock_response) as mock_post:
        record = logging.LogRecord(
            name="test_logger", level=logging.INFO, pathname="test.py", lineno=1, msg="x" * 5000, args=(), exc_info=None
        )

        handler.emit(record)

        # Should make two API calls for the split message
        assert mock_post.call_count == 2
        calls = mock_post.call_args_list

        # First chunk
        assert calls[0].kwargs["json"]["text"] == "x" * 4096
        # Second chunk
        assert calls[1].kwargs["json"]["text"] == "x" * 904
