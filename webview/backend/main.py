from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

# ВАЖНО: для FastAPI нужен генератор-зависимость, а не asynccontextmanager.
# Если в database/db.py есть session_generator — используем его алиасом как get_session.
from database.db import session_generator as get_session

from database import models
from utils.referrals import get_referral_stats
from utils.antifraud import check_and_update_ip
from bot_config import settings
from services import deposit as deposit_service
from admin.panel import router as admin_router

app = FastAPI(title="TONForge Web", version="1.0.0")

# CORS — оставляем, потом сузишь домены под прод
import os
ALLOWED_ORIGINS = [
    os.getenv("BASE_WEBAPP_URL", "https://tonforge-web.onrender.com"),
    "https://t.me",                # Telegram WebApp
    "https://web.telegram.org",    # веб-версия Telegram
    "http://localhost:3000",       # dev фронт
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Верхнеуровневые служебные эндпоинты ----------

@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict:
    """Health-check для Render."""
    return {"ok": True}

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    """Простая страница на корне (чтобы не было 404 на /)."""
    return """
    <!doctype html>
    <html lang="en">
      <head><meta charset="utf-8"><title>TONForge Web</title></head>
      <body style="font-family:ui-sans-serif,system-ui;margin:24px;line-height:1.5">
        <h1>TONForge Web</h1>
        <p>Backend is running.</p>
        <ul>
          <li>Status: <a href="/healthz">/healthz</a></li>
          <li>API: <a href="/api/health">/api/health</a></li>
          <li>Docs: <a href="/docs">/docs</a></li>
        </ul>
      </body>
    </html>
    """

# ---------- API (под префиксом /api) ----------

router = APIRouter(prefix="/api")


async def _fetch_user(
    session: AsyncSession, telegram_id: int, request: Request | None = None
) -> models.User:
    """Вернуть пользователя по telegram_id + базовый антифрод и блокировки."""
    result = await session.execute(
        select(models.User).where(models.User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    if request:
        await check_and_update_ip(session, user, request.client.host)
    if getattr(user, "is_blocked", False):
        raise HTTPException(status_code=403, detail="user_blocked")
    return user


@router.get("/health")
async def health() -> dict:
    """Простой сервисный эндпоинт (внутри /api)."""
    return {"status": "ok"}


@router.get("/balance")
async def balance(
    user_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> dict:
    user = await _fetch_user(session, user_id, request)
    cfg = await session.get(models.Config, 1)
    percent = cfg.daily_percent if cfg else 0.023
    deposits = await session.execute(
        select(models.Deposit.amount, models.Deposit.currency).where(
            models.Deposit.user_id == user.id, models.Deposit.is_active
        )
    )
    daily_income = sum(amount * percent for amount, _ in deposits.all())
    return {"balance": user.balance_ton, "daily_income": daily_income}


class GenerateLabelRequest(BaseModel):
    user_id: int
    method: str
    amount: float


@router.post("/generate_label")
async def generate_label(
    data: GenerateLabelRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await _fetch_user(session, data.user_id, request)

    method = data.method.upper()
    address = settings.ton_wallet if method == "TON" else settings.usdt_wallet
    dep = await deposit_service.create_deposit(
        session, user.id, data.amount, method, address if method == "USDT" else None
    )
    label = str(dep.id)
    return {"address": address, "label": label}


@router.get("/referrals")
async def referrals(
    user_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> dict:
    user = await _fetch_user(session, user_id, request)
    stats = await get_referral_stats(session, user.id)
    link = f"https://t.me/TONForgeBot?start={user_id}"
    earned = stats["bonus_ton"] + stats["bonus_usdt"]
    return {"link": link, "count": stats["invited"], "earned": earned}


@router.get("/profile/{telegram_id}")
async def get_profile(
    telegram_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> dict:
    user = await _fetch_user(session, telegram_id, request)
    stats = await get_referral_stats(session, user.id)
    return {
        "telegram_id": user.telegram_id,
        "balance_ton": user.balance_ton,
        "balance_usdt": user.balance_usdt,
        "referrals": stats,
    }


@router.get("/operations")
async def operations(
    user_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> dict:
    """История депозитов/выводов пользователя."""
    user = await _fetch_user(session, user_id, request)

    deposits = await session.execute(
        select(
            models.Deposit.amount,
            models.Deposit.currency,
            models.Deposit.created_at,
        ).where(models.Deposit.user_id == user.id)
    )
    withdrawals = await session.execute(
        select(
            models.Withdrawal.amount,
            models.Withdrawal.currency,
            models.Withdrawal.requested_at,
            models.Withdrawal.processed,
        ).where(models.Withdrawal.user_id == user.id)
    )
    return {
        "deposits": [
            {
                "amount": amount,
                "currency": currency,
                "created_at": created_at.isoformat() if created_at else None,
            }
            for amount, currency, created_at in deposits.all()
        ],
        "withdrawals": [
            {
                "amount": amount,
                "currency": currency,
                "requested_at": requested_at.isoformat() if requested_at else None,
                "processed": processed,
            }
            for amount, currency, requested_at, processed in withdrawals.all()
        ],
    }


# Регистрируем API и админку
app.include_router(router)
app.include_router(admin_router)
