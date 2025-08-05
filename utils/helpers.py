from __future__ import annotations

from decimal import Decimal
import re
from typing import Any, Dict
import httpx

TON_DECIMALS = 9

_TON_ADDRESS_RE = re.compile(r"^(?:EQ|UQ)[A-Za-z0-9_-]{46}$")
_TRON_ADDRESS_RE = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")


def format_ton(amount: int) -> str:
    """Convert amount from nanotons to TON string."""
    value = Decimal(amount) / Decimal(10**TON_DECIMALS)
    return f"{value.normalize():f}"


def parse_ton(value: str) -> int:
    """Parse TON string into nanotons."""
    dec = Decimal(value)
    return int((dec * (10 ** TON_DECIMALS)).to_integral_value())


async def fetch_json(url: str, params: Dict[str, Any] | None = None, headers: Dict[str, str] | None = None) -> Any:
    """Perform HTTP GET request and return JSON data."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()


def validate_ton_address(address: str) -> bool:
    """Check if provided string looks like a TON wallet address."""
    return bool(_TON_ADDRESS_RE.fullmatch(address))


def validate_tron_address(address: str) -> bool:
    """Check if provided string looks like a TRON wallet address."""
    return bool(_TRON_ADDRESS_RE.fullmatch(address))
