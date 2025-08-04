import asyncio
from services.income import accrue_daily_income

async def daily_job():
    while True:
        await accrue_daily_income()
        await asyncio.sleep(24 * 60 * 60)
