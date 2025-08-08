import asyncio
import httpx
import pytest
from services import ton


async def _raise_http_error(*args, **kwargs):
    request = httpx.Request("GET", "http://example.com")
    response = httpx.Response(status_code=404, request=request)
    raise httpx.HTTPStatusError("not found", request=request, response=response)


def test_check_deposit_http_error(monkeypatch):
    monkeypatch.setattr(ton, "fetch_json", _raise_http_error)

    async def run():
        amount = await ton.check_deposit("label", 1.0)
        assert amount == 0.0

    asyncio.run(run())
