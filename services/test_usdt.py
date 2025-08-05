import asyncio
import pytest
from services.usdt import check_deposit


def test_check_deposit_invalid_address():
    async def run():
        await check_deposit("invalid", "label", 1.0)
    with pytest.raises(ValueError):
        asyncio.run(run())
