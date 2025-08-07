from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import uuid4

from database.db import get_session
from database import models
from services.income import DAILY_PERCENT
from utils.referrals import get_referral_stats

app = FastAPI()
router = APIRouter(prefix="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@router.get("/health")
async def health() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}


@router.get("/balance")
async def balance(
    user_id: int, session: AsyncSession = Depends(get_session)
) -> dict:
    result = await session.execute(
        select(models.User).where(models.User.telegram_id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    deposits = await session.execute(
        select(models.Deposit.amount, models.Deposit.currency).where(
            models.Deposit.user_id == user.id, models.Deposit.is_active
        )
    )
    daily_income = sum(amount * DAILY_PERCENT for amount, _ in deposits.all())
    return {"balance": user.balance_ton, "daily_income": daily_income}


class GenerateLabelRequest(BaseModel):
    user_id: int
    method: str
    amount: float


@router.post("/generate_label")
async def generate_label(data: GenerateLabelRequest) -> dict:
    label = f"{data.user_id}-{uuid4().hex}"
    address = "TON_WALLET" if data.method.upper() == "TON" else "USDT_WALLET"
    return {"address": address, "label": label}


@router.get("/referrals")
async def referrals(
    user_id: int, session: AsyncSession = Depends(get_session)
) -> dict:
    result = await session.execute(
        select(models.User).where(models.User.telegram_id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    stats = await get_referral_stats(session, user.id)
    link = f"https://t.me/TONForgeBot?start={user_id}"
    earned = stats["bonus_ton"] + stats["bonus_usdt"]
    return {"link": link, "count": stats["invited"], "earned": earned}


@router.get("/profile/{telegram_id}")
async def get_profile(
    telegram_id: int, session: AsyncSession = Depends(get_session)
) -> dict:
    result = await session.execute(
        select(models.User).where(models.User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    stats = await get_referral_stats(session, user.id)
    return {
        "telegram_id": user.telegram_id,
        "balance_ton": user.balance_ton,
        "balance_usdt": user.balance_usdt,
        "referrals": stats,
    }


@router.get("/operations")
async def operations(
    user_id: int, session: AsyncSession = Depends(get_session)
) -> dict:
    """Return deposit and withdrawal history for the user."""
    result = await session.execute(
        select(models.User).where(models.User.telegram_id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

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
                "requested_at": requested_at.isoformat()
                if requested_at
                else None,
                "processed": processed,
            }
            for amount, currency, requested_at, processed in withdrawals.all()
        ],
    }
    
app.include_router(router
