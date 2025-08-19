from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import parse_qsl

from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.staticfiles import StaticFiles

from database.db import session_generator as get_session
from database import models
from utils.referrals import get_referral_stats
from utils.antifraud import check_and_update_ip
from services import deposit as deposit_service
from admin.panel import router as admin_router
from bot_config import settings

app = FastAPI(title="TONForge Web", version="1.0.0")

ALLOWED_ORIGINS = [
    os.getenv("BASE_WEBAPP_URL", "https://tonforge-web.onrender.com"),
    "https://t.me",
    "https://web.telegram.org",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict:
    return {"ok": True}

def _extract_telegram_id_from_init_data(request: Request) -> int | None:
    raw = request.headers.get("X-Telegram-Init-Data") or ""
    if not raw:
        return None
    try:
        data = dict(parse_qsl(raw, keep_blank_values=True))
        if "user" in data:
            u = json.loads(data["user"])
            tid = u.get("id")
            if isinstance(tid, int):
                return tid
    except Exception:
        return None
    return None

async def _get_or_create_user(session: AsyncSession, telegram_id: int, ip: str | None = None) -> models.User:
    res = await session.execute(select(models.User).where(models.User.telegram_id == telegram_id))
    user = res.scalar_one_or_none()
    if not user:
        user = models.User(telegram_id=telegram_id, language="en")
        session.add(user)
        await session.commit()
        await session.refresh(user)
    if ip:
        await check_and_update_ip(session, user, ip)
    if getattr(user, "is_blocked", False):
        raise HTTPException(status_code=403, detail="user_blocked")
    return user

def _bot_username() -> str:
    return getattr(settings, "bot_username", None) or os.getenv("BOT_USERNAME", "TONForge1_bot")

api = APIRouter(prefix="/api", tags=["api"])

@api.get("/health")
async def api_health() -> dict:
    return {"status": "ok"}

class DepositCreateIn(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str  # "TON" | "USDT"

@api.get("/me")
async def me(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    telegram_id = _extract_telegram_id_from_init_data(request)
    if telegram_id is None:
        q_user = request.query_params.get("user_id")
        if q_user and q_user.isdigit():
            telegram_id = int(q_user)
    if telegram_id is None:
        raise HTTPException(status_code=401, detail="no_telegram_context")

    user = await _get_or_create_user(session, telegram_id, request.client.host if request.client else None)

    cfg = await session.get(models.Config, 1)
    daily_percent = float(cfg.daily_percent if cfg else 0.023)
    min_deposit   = float(cfg.min_deposit if cfg else 10.0)
    min_withdraw  = float(cfg.min_withdraw if cfg else 50.0)

    ref_link = f"https://t.me/{_bot_username()}?start={user.telegram_id}"

    return {
        "telegram_id": user.telegram_id,
        "balance_ton": float(user.balance_ton or 0),
        "balance_usdt": float(user.balance_usdt or 0),
        "daily_percent": daily_percent,
        "min_deposit": min_deposit,
        "min_withdraw": min_withdraw,
        "referral_link": ref_link,
        "ton_wallet": getattr(settings, "ton_wallet", None),
        "usdt_wallet": getattr(settings, "usdt_wallet", None),
    }

@api.post("/deposits")
async def create_deposit_endpoint(
    data: DepositCreateIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    telegram_id = _extract_telegram_id_from_init_data(request)
    if telegram_id is None:
        q_user = request.query_params.get("user_id")
        if q_user and q_user.isdigit():
            telegram_id = int(q_user)
    if telegram_id is None:
        raise HTTPException(status_code=401, detail="no_telegram_context")

    user = await _get_or_create_user(session, telegram_id, request.client.host if request.client else None)

    cfg = await session.get(models.Config, 1)
    min_dep = float(cfg.min_deposit if cfg else 10.0)
    amount = float(data.amount)
    currency = data.currency.upper()
    if currency not in {"TON", "USDT"}:
        raise HTTPException(status_code=400, detail="currency_must_be_TON_or_USDT")
    if amount < min_dep:
        raise HTTPException(status_code=400, detail=f"min_deposit_is_{min_dep}")

    address = settings.ton_wallet if currency == "TON" else settings.usdt_wallet
    if not address:
        raise HTTPException(status_code=500, detail=f"{currency}_address_not_configured")

    dep = await deposit_service.create_deposit(
        session,
        user_id=user.id,
        amount=amount,
        currency=currency,
        address=None if currency == "TON" else address,
    )

    return {
        "id": dep.id,
        "amount": amount,
        "currency": currency,
        "address": address,
        "label": str(dep.id),
    }

class GenerateLabelRequest(BaseModel):
    user_id: int
    method: str
    amount: float

@api.post("/generate_label")
async def generate_label(
    data: GenerateLabelRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await _get_or_create_user(session, data.user_id, request.client.host if request.client else None)
    method = data.method.upper()
    address = settings.ton_wallet if method == "TON" else settings.usdt_wallet
    dep = await deposit_service.create_deposit(
        session, user.id, data.amount, method, address if method == "USDT" else None
    )
    return {"address": address, "label": str(dep.id)}

@api.get("/referrals")
async def referrals(
    user_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> dict:
    user = await _get_or_create_user(session, user_id, request.client.host if request.client else None)
    stats = await get_referral_stats(session, user.id)
    link = f"https://t.me/{_bot_username()}?start={user_id}"
    earned = stats["bonus_ton"] + stats["bonus_usdt"]
    return {"link": link, "count": stats["invited"], "earned": earned}

@api.get("/profile/{telegram_id}")
async def get_profile(
    telegram_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> dict:
    user = await _get_or_create_user(session, telegram_id, request.client.host if request.client else None)
    stats = await get_referral_stats(session, user.id)
    return {
        "telegram_id": user.telegram_id,
        "balance_ton": user.balance_ton,
        "balance_usdt": user.balance_usdt,
        "referrals": stats,
    }

@api.get("/operations")
async def operations(
    user_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> dict:
    user = await _get_or_create_user(session, user_id, request.client.host if request.client else None)
    deposits = await session.execute(
        select(models.Deposit.amount, models.Deposit.currency, models.Deposit.created_at)
        .where(models.Deposit.user_id == user.id)
    )
    withdrawals = await session.execute(
        select(models.Withdrawal.amount, models.Withdrawal.currency, models.Withdrawal.requested_at, models.Withdrawal.processed)
        .where(models.Withdrawal.user_id == user.id)
    )
    return {
        "deposits": [
            {"amount": a, "currency": c, "created_at": (dt.isoformat() if dt else None)}
            for a, c, dt in deposits.all()
        ],
        "withdrawals": [
            {"amount": a, "currency": c, "requested_at": (dt.isoformat() if dt else None), "processed": p}
            for a, c, dt, p in withdrawals.all()
        ],
    }

app.include_router(api)
app.include_router(admin_router)

# -------- Static frontend on root --------
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False, response_class=HTMLResponse)
    async def root_index():
        return "<h1>TONForge Web</h1><p>frontend not found.</p>"
