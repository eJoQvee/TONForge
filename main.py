import asyncio
import os
from aiogram import Bot, Dispatcher
from handlers import router  # в handlers/__init__.py должен быть router

async def main():
    bot = Bot(os.environ["BOT_TOKEN"])
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
