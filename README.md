# Python Telegram Logging

[![PyPI version](https://badge.fury.io/py/python-telegram-logging.svg)](https://badge.fury.io/py/python-telegram-logging)
[![CI](https://github.com/alcibiadescleinias/python-telegram-logging/actions/workflows/ci.yml/badge.svg)](https://github.com/alcibiadescleinias/python-telegram-logging/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/alcibiadescleinias/python-telegram-logging/branch/main/graph/badge.svg)](https://codecov.io/gh/alcibiadescleinias/python-telegram-logging)
[![Python Versions](https://img.shields.io/pypi/pyversions/python-telegram-logging.svg)](https://pypi.org/project/python-telegram-logging/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python logging handler that sends logs to Telegram with support for both synchronous and asynchronous operations.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
  - [Synchronous Usage](#synchronous-usage)
  - [Asynchronous Usage](#asynchronous-usage)
  - [Queued Usage (for synchronous handlers)](#queued-usage-for-synchronous-handlers)
- [Advanced Usage](#advanced-usage)
  - [Custom Formatting](#custom-formatting)
  - [Error Handling](#error-handling)
- [Handler Comparison](#handler-comparison)
- [Technical Details](#technical-details)
- [Requirements](#requirements)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Features

- 🚀 **Multiple Handler Types**:
  - `SyncTelegramHandler`: Synchronous handler using `requests`
  - `AsyncTelegramHandler`: Asynchronous handler with built-in queue using `aiohttp`
  - `QueuedTelegramHandler`: Thread-safe queued wrapper for synchronous handlers only (currently)

- 🔒 **Thread Safety**: All handlers are thread-safe and can be used in multi-threaded applications

- 🎨 **Formatting Support**:
  - HTML formatting
  - Markdown formatting
  - Custom formatters support

- 🛡️ **Error Handling**:
  - Rate limiting with configurable strategies (TODO)
  - Automatic message splitting for long logs
  - Custom error callbacks (in case if message is not sent, raised exception)

## Installation

```bash
pip install python-telegram-logging
```

## Quick Start

### Synchronous Usage

```python
import logging
from python_telegram_logging import SyncTelegramHandler, ParseMode

# Create and configure the handler
handler = SyncTelegramHandler(
    token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID",
    parse_mode=ParseMode.HTML
)

# Add it to your logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Use it!
logger.info("Hello from Python! 🐍")
```

### Asynchronous Usage

```python
import logging
from python_telegram_logging import AsyncTelegramHandler, ParseMode

# Create and configure the handler
handler = AsyncTelegramHandler(
    token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID",
    parse_mode=ParseMode.HTML
)

# Add it to your logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Use it in your async code!
logger.info("Hello from async Python! 🐍")
```

### Queued Usage (for synchronous handlers)

> ⚠️ **Important**: `QueuedTelegramHandler` is designed to work with synchronous handlers only. For asynchronous applications, use `AsyncTelegramHandler` directly as it already includes queue functionality.

```python
import logging
from python_telegram_logging import SyncTelegramHandler, QueuedTelegramHandler, ParseMode

# Create the base synchronous handler
base_handler = SyncTelegramHandler(
    token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID",
    parse_mode=ParseMode.HTML
)

# Wrap it in a queued handler for non-blocking operation
handler = QueuedTelegramHandler(base_handler, queue_size=1000)

# Add it to your logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Use it!
logger.info("Hello from queued logger! 🐍")
```

## Advanced Usage

### Custom Formatting

```python
import logging
from python_telegram_logging import SyncTelegramHandler, ParseMode

# Create a custom formatter
class HTMLFormatter(logging.Formatter):
    def format(self, record):
        return f"""
<b>{record.levelname}</b>: {record.getMessage()}
<code>
File: {record.filename}
Line: {record.lineno}
</code>
"""

# Use the custom formatter
handler = SyncTelegramHandler(
    token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID",
    parse_mode=ParseMode.HTML
)
handler.setFormatter(HTMLFormatter())
```

### Error Handling

```python
from python_telegram_logging import SyncTelegramHandler

def on_error(error: Exception):
    print(f"Failed to send log to Telegram: {error}")

handler = SyncTelegramHandler(
    token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID",
    error_callback=on_error
)
```

## Handler Comparison

| Feature | SyncTelegramHandler | AsyncTelegramHandler | QueuedTelegramHandler |
|---------|--------------------|--------------------|---------------------|
| Blocking | Yes | No | No |
| Thread-Safe | Yes | Yes | Yes |
| Dependencies | requests | aiohttp | - |
| Use Case | Simple scripts | Async applications | High-performance sync apps |
| Message Order | Guaranteed | Best-effort | Best-effort |
| Queue Support | No | Built-in | Yes (sync handlers only) |
| Handler Type | Sync | Async | Sync wrapper |

## Technical Details

- Rate limiting: Implements a token bucket algorithm to respect Telegram's rate limits
- Message splitting: Automatically splits messages longer than 4096 characters
- Thread safety: Uses appropriate synchronization primitives for each context
- Resource management: Proper cleanup of resources on handler close
- Error handling: Configurable error callbacks and retry strategies

## Requirements

- Python 3.8+
- `requests` >= 2.31.0
- `aiohttp` >= 3.8.6

## License

MIT License
