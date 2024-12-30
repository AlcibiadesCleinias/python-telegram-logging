# Python Telegram Logging

[![PyPI version](https://badge.fury.io/py/python-telegram-logging.svg)](https://badge.fury.io/py/
python-telegram-logging)
[![CI](https://github.com/bombon/python-telegram-logging/actions/workflows/ci.yml/badge.svg)]
(https://github.com/bombon/python-telegram-logging/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/bombon/python-telegram-logging/branch/main/graph/badge.svg)]
(https://codecov.io/gh/bombon/python-telegram-logging)
[![Python Versions](https://img.shields.io/pypi/pyversions/python-telegram-logging.svg)](https://
pypi.org/project/python-telegram-logging/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/
licenses/MIT)

A Python logging handler that sends logs to Telegram with support for both synchronous and asynchronous operations.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
  - [Synchronous Usage](#synchronous-usage)
  - [Asynchronous Usage](#asynchronous-usage)
  - [Queued Usage (for high-performance applications)](#queued-usage-for-high-performance-applications)
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
  - `AsyncTelegramHandler`: Asynchronous handler using `aiohttp`
  - `QueuedTelegramHandler`: Thread-safe queued handler for improved performance

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

### Queued Usage (for high-performance applications)

```python
import logging
from python_telegram_logging import AsyncTelegramHandler, QueuedTelegramHandler, ParseMode

# Create the base handler
base_handler = AsyncTelegramHandler(
    token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID",
    parse_mode=ParseMode.HTML
)

# Wrap it in a queued handler
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
| Use Case | Simple scripts | Async applications | High-performance apps |
| Message Order | Guaranteed | Best-effort | Best-effort |

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
