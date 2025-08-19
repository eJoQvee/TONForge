# webview/backend/api.py
from __future__ import annotations

import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from bot_config import settings
from database.db import get_session
from database import models
from .auth import get_current_user
from .schemas import ProfileResponse, DepositCreateRequest, DepositCreateResponse
from services import deposit as deposit_service

router = APIRouter()

BOT_USERNAME = os.getenv("BOT_USERNAME")  # желательно задать в Render web-сервисе

@router.get("/me", response_model=ProfileResponse)
async def get_me(
    session: AsyncSession = Depends(get_session),
    user: models.User = Depends(get_current_user),
):
    cfg = await session.get(models.Config, 1)
    daily = float(cfg.daily_percent if cfg else 0.023)
    min_dep = float(cfg.min_deposit if cfg else 10.0)
    min_wd  = float(cfg.min_withdraw if cfg else 50.0)
    wd_delay = int(cfg.withdraw_delay_hours if cfg else 24)

    ton_wallet = getattr(settings, "ton_wallet", os.getenv("TON_WALLET", ""))
    usdt_wallet = getattr(settings, "usdt_wallet", os.getenv("USDT_WALLET", ""))

    ref_link = None
    if BOT_USERNAME:
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user.id}"

    return ProfileResponse(
        telegram_id=user.telegram_id,
        language=user.language,
        balance_ton=float(user.balance_ton or 0.0),
        balance_usdt=float(user.balance_usdt or 0.0),
        daily_percent=daily,
        min_deposit=min_dep,
        min_withdraw=min_wd,
        withdraw_delay_hours=wd_delay,
        referral_link=ref_link,
        ton_wallet=ton_wallet,
        usdt_wallet=usdt_wallet,
    )

@router.post("/deposits", response_model=DepositCreateResponse)
async def create_deposit(
    payload: DepositCreateRequest,
    session: AsyncSession = Depends(get_session),
    user: models.User = Depends(get_current_user),
):
    currency = payload.currency.upper()
    if currency not in ("TON", "USDT"):
        raise HTTPException(status_code=400, detail="Currency must be TON or USDT")

    cfg = await session.get(models.Config, 1)
    min_dep = float(cfg.min_deposit if cfg else 10.0)
    if payload.amount < min_dep:
        raise HTTPException(status_code=400, detail=f"Min deposit is {min_dep}")

    ton_wallet = getattr(settings, "ton_wallet", os.getenv("TON_WALLET", ""))
    usdt_wallet = getattr(settings, "usdt_wallet", os.getenv("USDT_WALLET", ""))

    addr = ton_wallet if currency == "TON" else usdt_wallet
    if not addr:
        raise HTTPException(status_code=500, detail=f"{currency} wallet is not configured")

    # создаём запись депозита (НЕ активный)
    dep = await deposit_service.create_deposit(session, user.id, float(payload.amount), currency)

    # label для платежа
    if hasattr(deposit_service, "deposit_label"):
        label = deposit_service.deposit_label(dep, fallback_user_tg_id=user.telegram_id)
    else:
        label = str(dep.id)

    return DepositCreateResponse(
        deposit_id=dep.id,
        currency=currency,
        amount=float(payload.amount),
        address=addr,
        label=label,
        note="Send exact amount and put label in comment/memo.",
    )
