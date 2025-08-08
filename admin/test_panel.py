import asyncio
import sys
import types
from datetime import datetime

# ---- stub external packages ----
class DummyAPIRouter:
    def __init__(self, *args, **kwargs):
        pass
    def get(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def post(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
class DummyDepends:
    def __init__(self, *args, **kwargs):
        pass
class DummyHTTPException(Exception):
    def __init__(self, status_code=500, detail=""):
        super().__init__(detail)
class DummyStreamingResponse:
    def __init__(self, iterable, media_type=None, headers=None):
        self.body_iterator = iterable
class DummyHTTPBasic:
    pass
class DummyHTTPBasicCredentials:
    def __init__(self, **kwargs):
        pass

sys.modules["fastapi"] = types.SimpleNamespace(
    APIRouter=DummyAPIRouter, Depends=DummyDepends, HTTPException=DummyHTTPException
)
sys.modules["fastapi.security"] = types.SimpleNamespace(
    HTTPBasic=DummyHTTPBasic, HTTPBasicCredentials=DummyHTTPBasicCredentials
)
sys.modules["fastapi.responses"] = types.SimpleNamespace(
    StreamingResponse=DummyStreamingResponse
)

# dummy sqlalchemy select/func
class DummyQuery:
    def __init__(self, model):
        self.model = model
    def order_by(self, *args, **kwargs):
        return self
    def limit(self, *args, **kwargs):
        return self
    def __str__(self):
        return getattr(self.model, "__tablename__", "")

def dummy_select(model):
    return DummyQuery(model)

def dummy_sum(value):
    return value
sys.modules["sqlalchemy"] = types.SimpleNamespace(select=dummy_select, func=types.SimpleNamespace(sum=dummy_sum))

# stub bot_config and database modules
sys.modules["bot_config"] = types.SimpleNamespace(settings=types.SimpleNamespace(admin_password="pass"))
sys.modules["database.db"] = types.SimpleNamespace(get_session=lambda: None)

# simple models
class _Field:
    def desc(self):
        return None

class Deposit:
    __tablename__ = "deposits"
    created_at = _Field()
    def __init__(self, user_id, amount, currency, created_at):
        self.user_id = user_id
        self.amount = amount
        self.currency = currency
        self.created_at = created_at

class Withdrawal:
    __tablename__ = "withdrawals"
    requested_at = _Field()
    def __init__(self, user_id, amount, currency, requested_at, processed):
        self.user_id = user_id
        self.amount = amount
        self.currency = currency
        self.requested_at = requested_at
        self.processed = processed

class Config:
    def __init__(self, daily_percent=0.023, min_deposit=10, min_withdraw=50, delay=24, text=""):
        self.daily_percent = daily_percent
        self.min_deposit = min_deposit
        self.min_withdraw = min_withdraw
        self.withdraw_delay_hours = delay
        self.notification_text = text

models = types.SimpleNamespace(
    Deposit=Deposit,
    Withdrawal=Withdrawal,
    User=type("User", (), {}),
    Config=Config,
)
sys.modules["database"] = types.SimpleNamespace(models=models)

from admin.panel import logs, export_transactions, get_settings, update_settings

# ---- test helpers ----
class DummySession:
    def __init__(self, deposits, withdrawals, config=None):
        self._deposits = deposits
        self._withdrawals = withdrawals
        self._config = config or Config()
        
    async def execute(self, query):
        text = str(query)
        if "deposits" in text:
            return types.SimpleNamespace(scalars=lambda: types.SimpleNamespace(all=lambda: self._deposits))
        if "withdrawals" in text:
            return types.SimpleNamespace(scalars=lambda: types.SimpleNamespace(all=lambda: self._withdrawals))
        return types.SimpleNamespace(scalars=lambda: types.SimpleNamespace(all=lambda: []))

    async def get(self, model, _id):
        if model is Config:
            return self._config
        return None

    async def commit(self):
        return None


def _sample_data():
    dep = Deposit(1, 10.0, "TON", datetime.utcnow())
    wdr = Withdrawal(1, 5.0, "USDT", datetime.utcnow(), False)
    return [dep], [wdr]


def test_logs_returns_transactions():
    deposits, withdrawals = _sample_data()
    session = DummySession(deposits, withdrawals)
    async def run():
        result = await logs(session=session)
        assert result["deposits"][0]["amount"] == 10.0
        assert result["withdrawals"][0]["amount"] == 5.0
    asyncio.run(run())


def test_export_transactions_csv():
    deposits, withdrawals = _sample_data()
    session = DummySession(deposits, withdrawals)
    async def run():
        resp = await export_transactions(session=session)
        body = b"".join(
            chunk if isinstance(chunk, bytes) else chunk.encode() for chunk in resp.body_iterator
        )
        assert b"deposit" in body and b"withdrawal" in body
    asyncio.run(run())


def test_settings_roundtrip():
    cfg = Config(daily_percent=0.02, min_deposit=5)
    session = DummySession([], [], cfg)
    async def run():
        data = await get_settings(session=session)
        assert data["daily_percent"] == 0.02
        await update_settings({"daily_percent": 0.05, "min_deposit": 15}, session=session)
        assert cfg.daily_percent == 0.05
        assert cfg.min_deposit == 15
    asyncio.run(run())
