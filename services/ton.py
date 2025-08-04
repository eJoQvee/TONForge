import httpx
from bot_config import settings

TON_API_URL = "https://tonapi.io"  # пример; используйте нужный endpoint


async def check_deposit(label: str, min_amount: float) -> float:
    """
    Проверяет входящую транзакцию по label (payload/comment).
    Возвращает сумму, если транзакция найдена и >= min_amount.
    """
    headers = {"Authorization": f"Bearer {settings.ton_api_key}"} if settings.ton_api_key else {}
    async with httpx.AsyncClient() as client:
        # TODO: подставить реальный запрос к TonAPI
        resp = await client.get(f"{TON_API_URL}/v2/blockchain/transactions?comments={label}", headers=headers)
        data = resp.json()
        # Обработка ответа ...
    return 0.0
