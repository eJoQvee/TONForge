import httpx
from bot_config import settings

TRON_API_URL = "https://api.trongrid.io"  # пример

async def check_deposit(address: str, label: str, min_amount: float) -> float:
    """
    Проверка входящей USDT (TRC20) транзакции.
    """
    params = {"address": address, "token": "USDT"}
    headers = {"TRON-PRO-API-KEY": settings.tron_api_key} if settings.tron_api_key else {}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{TRON_API_URL}/v1/accounts/{address}/transactions/trc20", params=params, headers=headers)
        data = resp.json()
        # TODO: фильтрация по memo/label
    return 0.0
