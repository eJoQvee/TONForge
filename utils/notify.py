"""Utility helpers for sending notifications to a channel."""

from aiogram import Bot

from bot_config import settings


async def notify_channel(bot: Bot, text: str) -> None:
    """Send ``text`` to the configured channel if available."""
    if settings.channel_id:
        await bot.send_message(settings.channel_id, text)
