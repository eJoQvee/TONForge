import asyncio
import pytest
import sys
import types

sys.modules["aiogram"] = types.SimpleNamespace(Bot=object)
sys.modules["bot_config"] = types.SimpleNamespace(settings=types.SimpleNamespace(channel_id=None))

from utils.notify import notify_channel


class DummyBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


def test_notify_channel_noop(monkeypatch):
    bot = DummyBot()
    from bot_config import settings
    monkeypatch.setattr(settings, "channel_id", None, raising=False)

    async def run():
        await notify_channel(bot, "hi")

    asyncio.run(run())
    assert bot.sent == []


def test_notify_channel_sends(monkeypatch):
    bot = DummyBot()
    from bot_config import settings
    monkeypatch.setattr(settings, "channel_id", "123", raising=False)

    async def run():
        await notify_channel(bot, "hi")

    asyncio.run(run())
    assert bot.sent == [("123", "hi")]
