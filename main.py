import asyncio
import logging
import os
import signal
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from bot_config import settings
from handlers import start, help, profile, withdraw, deposit, referral, panel, errors
from database.migrate import migrate
from database.db import engine
from utils.scheduler import daily_job, deposit_job

bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
logger = logging.getLogger(__name__)

dp.include_router(start.router)
dp.include_router(help.router)
dp.include_router(profile.router)
dp.include_router(withdraw.router)
dp.include_router(deposit.router)
dp.include_router(referral.router)
dp.include_router(panel.router)
dp.include_router(errors.router)


async def handle(_request: web.Request) -> web.Response:
    """Simple health endpoint for Render."""
    return web.Response(text="OK")


async def start_web() -> None:
    """Start a minimal web server so Render detects an open port."""
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    try:
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
    except OSError as exc:
        logger.exception("Failed to bind web server to port %s", port)
        raise
    else:
        logger.info("Web server started on port %s", port)


async def main() -> None:
    await start_web()
    # Ensure database tables exist before starting
    await migrate()
    # Ensure bot uses long polling by removing any existing webhook
    await bot.delete_webhook(drop_pending_updates=True)
    
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    tasks = [
        asyncio.create_task(start_web()),
        asyncio.create_task(dp.start_polling(bot)),
        asyncio.create_task(daily_job()),
        asyncio.create_task(deposit_job(bot)),
    ]

    await stop_event.wait()

    stop_polling = dp.stop_polling()
    if asyncio.iscoroutine(stop_polling):
        await stop_polling

    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    await bot.session.close()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
