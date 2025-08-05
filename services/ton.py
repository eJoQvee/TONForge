import httpx
import logging
from bot_config import settings
from utils.helpers import fetch_json

TON_API_URL = "https://tonapi.io"  # пример; используйте нужный endpoint

logger = logging.getLogger(__name__)


async def check_deposit(label: str, min_amount: float) -> float:
    """
    Проверяет входящую транзакцию по label (payload/comment).
    Возвращает сумму, если транзакция найдена и >= min_amount.
    """
    headers = {"Authorization": f"Bearer {settings.ton_api_key}"} if settings.ton_api_key else None
    params = {"comments": label}
    data = await fetch_json(
        f"{TON_API_URL}/v2/blockchain/transactions",
        params=params,
        headers=headers,
    )
    # Обработка ответа ...
    return 0.0


async def get_transaction_amount(tx_hash: str) -> float:
    """Fetch the amount of TON transferred in a transaction.

    Args:
        tx_hash: Transaction hash in hex/base64 format.

    Returns:
        Amount in TON as a float. Returns 0.0 on failure.
    """
    headers = {"Authorization": f"Bearer {settings.ton_api_key}"} if settings.ton_api_key else {}
    url = f"{TON_API_URL}/v2/blockchain/transactions/{tx_hash}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch TON transaction %s: %s", tx_hash, exc)
        return 0.0

    value = (
        data.get("transaction", {})
        .get("in_msg", {})
        .get("value")
    )
    if value is None:
        logger.warning("Transaction %s has no value field", tx_hash)
        return 0.0

    try:
        return int(value) / 1_000_000_000  # convert from nanoTON
    except (TypeError, ValueError):
        logger.error("Invalid value in transaction %s: %s", tx_hash, value)
        return 0.0
