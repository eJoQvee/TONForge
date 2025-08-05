import logging
from bot_config import settings
from utils.helpers import fetch_json, validate_tron_address
import httpx

TRON_API_URL = "https://api.trongrid.io"  # пример

logger = logging.getLogger(__name__)


async def check_deposit(address: str, label: str, min_amount: float) -> float:
    """Check incoming USDT (TRC20) transaction.

    Args:
        address: Recipient TRON address.
        label:   Memo/label that should be attached to the transaction.
        min_amount: Minimal amount (in USDT) to consider the deposit valid.

    Returns:
        Amount received in USDT if a matching transaction is found, otherwise
        ``0.0``.
    """
    
    if not validate_tron_address(address):
        raise ValueError("Invalid TRON wallet address")
    
    params = {
        "address": address,
        "limit": 50,
        "order_by": "block_timestamp,desc",
    }
    headers = (
        {"TRON-PRO-API-KEY": settings.tron_api_key}
        if settings.tron_api_key
        else None
    )
        data = await fetch_json(
        f"{TRON_API_URL}/v1/accounts/{address}/transactions/trc20",
        params=params,
        headers=headers,
    )
    
    transactions = data.get("data") or []
    for tx in transactions:
        # Decode memo if present (hex string)
        memo_hex = tx.get("data") or ""
        if memo_hex.startswith("0x"):
            memo_hex = memo_hex[2:]
        try:
            memo = bytes.fromhex(memo_hex).decode("utf-8")
        except Exception:
            memo = ""
        if memo != label:
            continue

        if tx.get("token_info", {}).get("symbol") != "USDT":
            continue

        value = tx.get("value") or tx.get("result", {}).get("value")
        if value is None:
            continue
        try:
            amount = int(value) / 1_000_000  # USDT has 6 decimals
        except (TypeError, ValueError):
            continue

        if amount >= min_amount:
            return amount

    return 0.0


async def get_transaction_amount(tx_hash: str) -> float:
    """Fetch the amount of USDT (TRC20) transferred in a transaction.

    Args:
        tx_hash: TRON transaction hash.

    Returns:
        Amount in USDT as float. Returns 0.0 on failure.
    """
    headers = {"TRON-PRO-API-KEY": settings.tron_api_key} if settings.tron_api_key else {}
    url = f"{TRON_API_URL}/v1/transactions/{tx_hash}/events"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch TRON transaction %s: %s", tx_hash, exc)
        return 0.0

    events = data.get("data") or []
    for event in events:
        token_info = event.get("token_info") or {}
        if token_info.get("symbol") == "USDT":
            value = event.get("result", {}).get("value")
            if value is None:
                continue
            try:
                return int(value) / 1_000_000  # USDT has 6 decimals
            except (TypeError, ValueError):
                logger.error("Invalid value in transaction %s: %s", tx_hash, value)
                return 0.0

    logger.warning("USDT event not found for transaction %s", tx_hash)
    return 0.0
