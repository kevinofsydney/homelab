#!/usr/bin/env python3
"""Offline synthetic test: a chat filter must also reject group callbacks.

Use the pinned Hermes environment. This bare adapter exercises only its fallback
callback path and does not prove how a configured live gateway behaves.
"""
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

os.environ['TELEGRAM_ALLOWED_USERS'] = '111'
for key in ('GATEWAY_ALLOWED_USERS', 'GATEWAY_ALLOW_ALL_USERS',
            'TELEGRAM_ALLOW_ALL_USERS', 'TELEGRAM_GROUP_ALLOWED_USERS',
            'TELEGRAM_GROUP_ALLOWED_CHATS'):
    os.environ.pop(key, None)

from gateway.config import Platform, PlatformConfig
from plugins.platforms.telegram.adapter import TelegramAdapter

adapter = object.__new__(TelegramAdapter)
adapter.platform = Platform.TELEGRAM
adapter.config = PlatformConfig(enabled=True, token='synthetic', extra={'allowed_chats': ['111']})
adapter._bot = SimpleNamespace(id=999, username='synthetic')
adapter._message_handler = AsyncMock()
accepted = adapter._is_callback_user_authorized('111', chat_id='-100', chat_type='group')
print('FAIL: owner group callback accepted' if accepted else 'PASS: owner group callback denied')
raise SystemExit(1 if accepted else 0)
