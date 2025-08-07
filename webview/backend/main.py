from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database import models
from utils.referrals import get_referral_stats

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.get("/balance")
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


@app.post("/generate_label")
async def generate_label(data: GenerateLabelRequest) -> dict:
    label = f"{data.user_id}-{uuid4().hex}"
    address = "TON_WALLET" if data.method.upper() == "TON" else "USDT_WALLET"
    return {"address": address, "label": label}


@app.get("/referrals")
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


@app.get("/profile/{telegram_id}")
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
