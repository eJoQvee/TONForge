import pytest

from utils.notify import notify_channel


class DummyBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


@pytest.mark.asyncio
async def test_notify_channel_noop(monkeypatch):
    bot = DummyBot()
    from bot_config import settings
    monkeypatch.setattr(settings, "channel_id", None)
    await notify_channel(bot, "hi")
    assert bot.sent == []


@pytest.mark.asyncio
async def test_notify_channel_sends(monkeypatch):
    bot = DummyBot()
    from bot_config import settings
    monkeypatch.setattr(settings, "channel_id", "123")
    await notify_channel(bot, "hi")
    assert bot.sent == [("123", "hi")]
