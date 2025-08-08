import logging
from bot_config import settings
from utils.helpers import fetch_json
import httpx

TON_API_URL = "https://tonapi.io"  # пример; используйте нужный endpoint

logger = logging.getLogger(__name__)


async def check_deposit(label: str, min_amount: float) -> float:
    """Check an incoming TON transaction by comment payload.

    Args:
        label: Text comment that should be attached to the incoming message.
        min_amount: Minimal amount (in TON) required for a valid deposit.

    Returns:
        Amount received in TON if a matching transaction is found,
        otherwise ``0.0``.
    """
    
    headers = (
        {"Authorization": f"Bearer {settings.ton_api_key}"}
        if settings.ton_api_key
        else None
    )
    params = {"limit": 20}
    url = f"{TON_API_URL}/v2/blockchain/accounts/{settings.ton_wallet}/transactions"
    try:
        data = await fetch_json(
            url,
            params=params,
            headers=headers,
        )
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch TON transactions: %s", exc)
        return 0.0
    
    transactions = data.get("transactions") or []
    for tx in transactions:
        in_msg = tx.get("in_msg") or {}
        comment = in_msg.get("comment") or ""
        if comment != label:
            continue
        value = in_msg.get("value")
        if value is None:
            continue
        try:
            amount = int(value) / 1_000_000_000  # convert from nanoTON
        except (TypeError, ValueError):
            continue
        if amount >= min_amount:
            return amount

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
