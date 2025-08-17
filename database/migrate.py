import asyncio
from importlib import import_module

from database.db import engine, Base

def _import_models():
    """
    Импортируем все модели, чтобы Base.metadata их увидела.
    Подстрой список под свои файлы, если нужно. Пробуем мягко.
    """
    candidates = (
        "database.models",              # общий сборщик, если есть
        "database.models.user",
        "database.models.deposit",
        "database.models.transaction",
        "database.models.referral",
    )
    for mod in candidates:
        try:
            import_module(mod)
        except Exception:
            pass  # модуль может отсутствовать — ок

async def _run_async():
    _import_models()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def migrate():
    """
    Обёртка: можно импортировать и вызывать из кода, если нужно.
    Если цикл событий уже идёт — вернёт Task.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_run_async())
    else:
        return asyncio.create_task(_run_async())

if __name__ == "__main__":
    asyncio.run(_run_async())
