from aiogram import Bot
import os
CHANNEL_ID = os.getenv("CHANNEL_ID")  # например, "@tonforge_notifications"

async def notify_deposit(bot: Bot, user_id: int, amount: float, currency: str):
    if not CHANNEL_ID:
        return
    await bot.send_message(CHANNEL_ID, f"Входящий депозит: пользователь {user_id}, {amount} {currency}")

async def notify_withdraw_request(bot: Bot, user_id: int, amount: float, currency: str):
    if not CHANNEL_ID:
        return
    await bot.send_message(CHANNEL_ID, f"Заявка на вывод: {user_id}, {amount} {currency}")
