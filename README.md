# Python Telegram Logging

[![PyPI version](https://badge.fury.io/py/python-telegram-logging.svg)](https://badge.fury.io/py/python-telegram-logging)
[![CI](https://github.com/bombon/python-telegram-logging/actions/workflows/ci.yml/badge.svg)](https://github.com/bombon/python-telegram-logging/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/bombon/python-telegram-logging/branch/main/graph/badge.svg)](https://codecov.io/gh/bombon/python-telegram-logging)
[![Python Versions](https://img.shields.io/pypi/pyversions/python-telegram-logging.svg)](https://pypi.org/project/python-telegram-logging/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install python-telegram-logging
```

## Usage
Check [examples](./examples) for more examples or, **tl;dr**:

```python
import logging
from pytelegram_logging.handlers import SyncTelegramHandler
from pytelegram_logging.enums import ParseMode
from pytelegram_logging.queue import QueuedTelegramHandler

# Create a handler
handler = SyncTelegramHandler(
    token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID",
    parse_mode=ParseMode.HTML,
    disable_notification=True
)

# Optionally wrap it in a queue handler (recommended)
queued_handler = QueuedTelegramHandler(handler)

# Add it to your logger
logger = logging.getLogger(__name__)
logger.addHandler(queued_handler)

# Log messages
logger.info("Hello from Telegram logging!")
```

TODO: automatic CHANGELOG.md.
