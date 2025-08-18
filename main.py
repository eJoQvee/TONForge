import asyncio
import logging
import os
import signal
import sys
from typing import List

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from handlers import router  # корневой агрегатор роутеров

# Логирование — минимум, чтобы видеть старт/останов
logger = logging.getLogger("tonforge.bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


async def _maybe_run_migrations() -> None:
    """
    Миграции из воркера по умолчанию отключены.
    Включить можно через ENV RUN_MIGRATIONS_ON_START=1.
    """
    if os.getenv("RUN_MIGRATIONS_ON_START") != "1":
        return
    try:
        from database.migrate import migrate
        logger.info("Running DB migrations from worker...")
        await migrate()  # у нас асинхронная обёртка
        logger.info("DB migrations completed.")
    except Exception:
        logger.exception("DB migrations failed in worker")


async def _maybe_start_scheduler(bot: Bot, tasks: List[asyncio.Task]) -> None:
    """
    Запустить фоновые задачи только если ENABLE_SCHEDULER=1.
    Ожидаются функции daily_job() и deposit_job(bot) в utils.scheduler.
    """
    if os.getenv("ENABLE_SCHEDULER") != "1":
        logger.info("Scheduler is disabled (ENABLE_SCHEDULER!=1).")
        return
    try:
        from utils.scheduler import daily_job, deposit_job
    except Exception:
        logger.exception("Scheduler import failed (utils.scheduler)")
        return

    logger.info("Starting scheduler tasks...")
    tasks.append(asyncio.create_task(daily_job(), name="daily_job"))
    tasks.append(asyncio.create_task(deposit_job(bot), name="deposit_job"))


async def main() -> None:
    # --- Токен только из BOT_TOKEN ---
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("[FATAL] BOT_TOKEN is not set in worker ENV.", file=sys.stderr)
        raise SystemExit(1)

    # --- Бот и диспетчер ---
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)

    # --- Миграции (по флагу) ---
    await _maybe_run_migrations()

    # --- Убираем вебхук перед polling, чистим хвост апдейтов ---
    await bot.delete_webhook(drop_pending_updates=True)

    # --- Команды в меню бота ---
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запуск/регистрация"),
            BotCommand(command="help", description="Помощь"),
            BotCommand(command="profile", description="Профиль"),
            BotCommand(command="withdraw", description="Вывод средств"),
            BotCommand(command="balance", description="Баланс и дневной доход"),
        ]
    )

    # --- Корректная остановка по сигналам ---
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _on_signal() -> None:
        logger.info("Stop signal received.")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal)
        except NotImplementedError:
            # На Windows signal handlers не поддерживаются — не критично
            pass

    # --- Запуск задач ---
    tasks: List[asyncio.Task] = []
    tasks.append(
        asyncio.create_task(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            name="polling",
        )
    )

    # Фоновые задачи по флагу
    await _maybe_start_scheduler(bot, tasks)

    logger.info("Bot started. Waiting for stop...")
    await stop_event.wait()

    # --- Грациозная остановка ---
    logger.info("Stopping polling...")
    stop_polling = dp.stop_polling()
    if asyncio.iscoroutine(stop_polling):
        await stop_polling

    logger.info("Cancelling background tasks...")
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    # Закрываем сетевые ресурсы
    try:
        from database.db import engine
    except Exception:
        engine = None

    await bot.session.close()
    if engine is not None:
        await engine.dispose()

    logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
