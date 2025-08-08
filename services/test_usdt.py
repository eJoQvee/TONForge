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
    settings=types.SimpleNamespace(tron_api_key=None)
)

from services.usdt import check_deposit


def test_check_deposit_invalid_address():
    async def run():
        await check_deposit("invalid", "label", 1.0)
    with pytest.raises(ValueError):
        asyncio.run(run())


async def _raise_http_error(*args, **kwargs):
    raise DummyHTTPStatusError()


def test_check_deposit_http_error(monkeypatch):
    monkeypatch.setattr("services.usdt.validate_tron_address", lambda addr: True)
    monkeypatch.setattr("services.usdt.fetch_json", _raise_http_error)

    async def run():
        amount = await check_deposit("T" * 34, "label", 1.0)
        assert amount == 0.0

    asyncio.run(run())


def test_check_deposit_includes_api_key(monkeypatch):
    monkeypatch.setattr("services.usdt.validate_tron_address", lambda addr: True)
    monkeypatch.setattr("services.usdt.settings", type("obj", (), {"tron_api_key": "test-key"}))

    captured = {}

    async def fake_fetch_json(url, params=None, headers=None):
        captured["headers"] = headers
        return {"data": []}

    monkeypatch.setattr("services.usdt.fetch_json", fake_fetch_json)

    async def run():
        amount = await check_deposit("T" * 34, "label", 1.0)
        assert amount == 0.0

    asyncio.run(run())
    assert captured["headers"]["TRON-PRO-API-KEY"] == "test-key"

