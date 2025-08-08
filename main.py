import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from bot_config import settings
from handlers import start, help, profile, withdraw, deposit, referral, panel
from database.migrate import migrate
from utils.scheduler import daily_job, deposit_job

bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(help.router)
dp.include_router(profile.router)
dp.include_router(withdraw.router)
dp.include_router(deposit.router)
dp.include_router(referral.router)
dp.include_router(panel.router)


async def handle(_request: web.Request) -> web.Response:
    """Simple health endpoint for Render."""
    return web.Response(text="OK")


async def start_web() -> None:
    """Start a minimal web server so Render detects an open port."""
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main() -> None:
    # Ensure database tables exist before starting
    await migrate()
    # Ensure bot uses long polling by removing any existing webhook
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(
        start_web(),
        dp.start_polling(bot),
        daily_job(),
        deposit_job(bot),
    )


if __name__ == "__main__":
    asyncio.run(main())
