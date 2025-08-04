import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from bot_config import settings
from handlers import start, help, profile, withdraw

bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(help.router)
dp.include_router(profile.router)
dp.include_router(withdraw.router)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
