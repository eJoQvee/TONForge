from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

# ВАЖНО: используем общий Base из database.db
from database.db import Base


# === USERS ===================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    language: Mapped[str] = mapped_column(String(5), default="en")

    # Балансы по двум валютам
    balance_ton: Mapped[float] = mapped_column(Float, default=0.0)
    balance_usdt: Mapped[float] = mapped_column(Float, default=0.0)

    # Рефералка: кто пригласил
    referrer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Антифрод/бан
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_ip: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# === DEPOSITS ================================================
class Deposit(Base):
    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8))  # "TON" | "USDT"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # адрес для оплаты (например, USDT TRC-20) — ИМЕННО ЭТОГО ПОЛЯ НЕ ХВАТАЛО
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# === WITHDRAWALS =============================================
class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8))  # "TON" | "USDT"
    processed: Mapped[bool] = mapped_column(Boolean, default=False)

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# === INVITES (реферальные связи) =============================
class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    invited_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    level: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# === TRANSACTIONS (входящие пополнения) ======================
class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("tx_hash", name="uq_transactions_tx_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8))  # "TON" | "USDT"

    tx_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # "TON" | "TRON" и т.п.
    label: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    status: Mapped[str] = mapped_column(String, default="confirmed")  # на вырост

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# === REFERRAL PAYOUTS (выплаты по рефералке) =================
class ReferralPayout(Base):
    __tablename__ = "referral_payouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)  # чей депозит
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)    # кому бонус
    level: Mapped[int] = mapped_column(Integer)  # 1..5

    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8))  # "TON" | "USDT"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# === SETTINGS (Config) ======================================
class Config(Base):
    __tablename__ = "settings"  # таблица называется settings — оставляем так

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    daily_percent: Mapped[float] = mapped_column(Float, default=0.023)
    min_deposit: Mapped[float] = mapped_column(Float, default=10.0)
    min_withdraw: Mapped[float] = mapped_column(Float, default=50.0)
    withdraw_delay_hours: Mapped[int] = mapped_column(Integer, default=24)

    notification_text: Mapped[str] = mapped_column(String, default="")
