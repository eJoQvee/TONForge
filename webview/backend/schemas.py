from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List

class ProfileResponse(BaseModel):
    telegram_id: int
    language: str
    balance_ton: float
    balance_usdt: float
    daily_percent: float
    min_deposit: float
    min_withdraw: float
    withdraw_delay_hours: int
    referral_link: Optional[str] = None
    ton_wallet: Optional[str] = None
    usdt_wallet: Optional[str] = None

class DepositCreateRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str  # "TON" | "USDT"

class DepositCreateResponse(BaseModel):
    deposit_id: int
    currency: str
    amount: float
    address: str
    label: str
    note: str = "Send exact amount and put label in comment/memo."
