from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, ForeignKey, Boolean, DateTime, func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    language: Mapped[str] = mapped_column(String(2), default="ru")
    balance_ton: Mapped[float] = mapped_column(Float, default=0)
    balance_usdt: Mapped[float] = mapped_column(Float, default=0)
    referrer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    referrer = relationship("User", remote_side=[id])
    deposits = relationship("Deposit", back_populates="user", cascade="all, delete-orphan")
    withdrawals = relationship("Withdrawal", back_populates="user", cascade="all, delete-orphan")
    invites = relationship("Invite", back_populates="user", cascade="all, delete-orphan")


class Deposit(Base):
    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float]
    currency: Mapped[str] = mapped_column(String(4))  # TON/USDT
    # Address where the deposit was sent (used for USDT/TRON deposits)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User")


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float]
    currency: Mapped[str] = mapped_column(String(4))
    # Destination wallet for the withdrawal
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    requested_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    user = relationship("User")
    

class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    external_url: Mapped[str] = mapped_column(String)
    short_link: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("User", back_populates="invites")
