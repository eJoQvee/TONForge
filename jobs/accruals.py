import asyncio
from datetime import datetime, timezone
from database.db import async_session  # или get_session — как удобнее

DAILY_RATE = 0.023  # 2.3%/день

async def process():
    async with async_session() as session:
        # TODO:
        # 1) выбрать активные депозиты
        # 2) посчитать процент и начислить
        # 3) зафиксировать историю, если нужно
        # 4) commit
        print("[ACCRUALS] done at", datetime.now(timezone.utc).isoformat())

if __name__ == "__main__":
    asyncio.run(process())
