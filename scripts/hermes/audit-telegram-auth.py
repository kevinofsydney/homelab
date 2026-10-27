#!/usr/bin/env python3
"""Offline diagnostic for pinned Hermes Telegram adapter paths; uses synthetic IDs.

Run from the Hermes source directory with its installed Python environment. This
is not an end-to-end gateway, configuration-merging, or Telegram network test.
"""
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

# Synthetic allowlist; never read or print a real bot token.
os.environ['TELEGRAM_ALLOWED_USERS'] = '111'
for key in ('GATEWAY_ALLOWED_USERS', 'GATEWAY_ALLOW_ALL_USERS',
            'TELEGRAM_ALLOW_ALL_USERS', 'TELEGRAM_GROUP_ALLOWED_USERS',
            'TELEGRAM_GROUP_ALLOWED_CHATS'):
    os.environ.pop(key, None)

from gateway.config import Platform, PlatformConfig
from plugins.platforms.telegram.adapter import TelegramAdapter

adapter = object.__new__(TelegramAdapter)
adapter.platform = Platform.TELEGRAM
adapter.config = PlatformConfig(enabled=True, token='synthetic', extra={
    'allow_from': ['111'], 'group_allow_from': [],
})
adapter._bot = SimpleNamespace(id=999, username='synthetic')
adapter._message_handler = AsyncMock()


def message(uid, chat_type):
    return SimpleNamespace(
        message_id=1, text='synthetic', caption=None, entities=[], caption_entities=[],
        message_thread_id=None, is_topic_message=False,
        chat=SimpleNamespace(id=uid if chat_type == 'private' else -100,
                             type=chat_type, title='synthetic', is_forum=False),
        from_user=SimpleNamespace(id=uid, full_name='synthetic', first_name='synthetic'),
        reply_to_message=None,
    )


checks = {
    'owner private message allowed': adapter._is_user_authorized_from_message(message(111, 'private')),
    'other private message denied': not adapter._is_user_authorized_from_message(message(222, 'private')),
    'owner group message denied': not adapter._is_user_authorized_from_message(message(111, 'group')),
    # Tests the adapter's env fallback, not the live runner's injected callback.
    'owner group callback denied': not adapter._is_callback_user_authorized('111', chat_id='-100', chat_type='group'),
}
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}: {name}")
raise SystemExit(0 if all(checks.values()) else 1)
