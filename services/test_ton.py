import asyncio
import sys
import types
import pytest


class DummyHTTPError(Exception):
    pass


class DummyHTTPStatusError(DummyHTTPError):
    pass


dummy_httpx = types.SimpleNamespace(
    HTTPError=DummyHTTPError,
    HTTPStatusError=DummyHTTPStatusError,
)
sys.modules["httpx"] = dummy_httpx
sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda: None)
sys.modules["bot_config"] = types.SimpleNamespace(
    settings=types.SimpleNamespace(ton_api_key=None, ton_wallet="wallet")
)

from services import ton

async def _raise_http_error(*args, **kwargs):
    raise DummyHTTPStatusError()


def test_check_deposit_http_error(monkeypatch):
    monkeypatch.setattr(ton, "fetch_json", _raise_http_error)

    async def run():
        amount = await ton.check_deposit("label", 1.0)
        assert amount == 0.0

    asyncio.run(run())
    

def test_check_deposit_includes_api_key(monkeypatch):
    """Ensure TON API key is passed both in headers and params."""

    monkeypatch.setattr(ton.settings, "ton_api_key", "test-key")
    monkeypatch.setattr(ton.settings, "ton_wallet", "test-wallet")

    captured = {}

    async def fake_fetch_json(url, params=None, headers=None):
        captured["params"] = params
        captured["headers"] = headers
        return {"transactions": []}

    monkeypatch.setattr(ton, "fetch_json", fake_fetch_json)

    async def run():
        amount = await ton.check_deposit("label", 1.0)
        assert amount == 0.0

    asyncio.run(run())

    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["headers"]["X-API-Key"] == "test-key"
    assert captured["params"]["api_key"] == "test-key"
