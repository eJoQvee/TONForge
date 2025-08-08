from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select, func
import csv
import io
from datetime import datetime

from bot_config import settings
from database.db import get_session
from database import models

router = APIRouter(prefix="/admin")
security = HTTPBasic()


def auth(credentials: HTTPBasicCredentials):
    if credentials.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@router.get("/stats", dependencies=[Depends(auth)])
async def stats(session=Depends(get_session)):
    users_count = await session.scalar(models.User.__table__.count())
    deposits_sum = await session.scalar(models.Deposit.__table__.c.amount.sum())
    pending_withdrawals = await session.scalar(
        select(func.sum(models.Withdrawal.amount)).where(models.Withdrawal.processed.is_(False))
    )
    return {
        "users": users_count,
        "deposits": deposits_sum,
        "pending_withdrawals": pending_withdrawals or 0,
    }


@router.get("/settings", dependencies=[Depends(auth)])
async def get_settings(session=Depends(get_session)):
    cfg = await session.get(models.Config, 1)
    if not cfg:
        return {}
    return {
        "daily_percent": cfg.daily_percent,
        "min_deposit": cfg.min_deposit,
        "min_withdraw": cfg.min_withdraw,
        "withdraw_delay_hours": cfg.withdraw_delay_hours,
        "notification_text": cfg.notification_text,
    }


@router.post("/settings", dependencies=[Depends(auth)])
async def update_settings(data: dict, session=Depends(get_session)):
    cfg = await session.get(models.Config, 1)
    if not cfg:
        cfg = models.Config()
        session.add(cfg)
    for field in [
        "daily_percent",
        "min_deposit",
        "min_withdraw",
        "withdraw_delay_hours",
        "notification_text",
    ]:
        if field in data:
            setattr(cfg, field, data[field])
    await session.commit()
    return {"status": "updated"}


@router.get("/users", dependencies=[Depends(auth)])
async def list_users(session=Depends(get_session)):
    result = await session.execute(select(models.User))
    users = [
        {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "blocked": u.is_blocked,
            "balance_ton": u.balance_ton,
            "balance_usdt": u.balance_usdt,
        }
        for u in result.scalars().all()
    ]
    return {"users": users}


@router.post("/block/{user_id}", dependencies=[Depends(auth)])
async def block_user(user_id: int, session=Depends(get_session)):
    user = await session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="not_found")
    user.is_blocked = True
    await session.commit()
    return {"status": "blocked"}


@router.post("/unblock/{user_id}", dependencies=[Depends(auth)])
async def unblock_user(user_id: int, session=Depends(get_session)):
    user = await session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="not_found")
    user.is_blocked = False
    await session.commit()
    return {"status": "unblocked"}


@router.get("/export/users", dependencies=[Depends(auth)])
async def export_users(session=Depends(get_session)):
    result = await session.execute(select(models.User))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "telegram_id", "blocked", "balance_ton", "balance_usdt"])
    for u in result.scalars().all():
        writer.writerow([u.id, u.telegram_id, u.is_blocked, u.balance_ton, u.balance_usdt])
    output.seek(0)
    headers = {"Content-Disposition": "attachment; filename=users.csv"}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)


@router.get("/logs", dependencies=[Depends(auth)])
async def logs(session=Depends(get_session)):
    dep_result = await session.execute(
        select(models.Deposit).order_by(models.Deposit.created_at.desc()).limit(50)
    )
    with_result = await session.execute(
        select(models.Withdrawal).order_by(models.Withdrawal.requested_at.desc()).limit(50)
    )
    deposits = [
        {
            "user_id": d.user_id,
            "amount": d.amount,
            "currency": d.currency,
            "created_at": d.created_at.isoformat() if isinstance(d.created_at, datetime) else None,
        }
        for d in dep_result.scalars().all()
    ]
    withdrawals = [
        {
            "user_id": w.user_id,
            "amount": w.amount,
            "currency": w.currency,
            "requested_at": w.requested_at.isoformat() if isinstance(w.requested_at, datetime) else None,
            "processed": w.processed,
        }
        for w in with_result.scalars().all()
    ]
    return {"deposits": deposits, "withdrawals": withdrawals}


@router.get("/export/transactions", dependencies=[Depends(auth)])
async def export_transactions(session=Depends(get_session)):
    dep_result = await session.execute(select(models.Deposit))
    with_result = await session.execute(select(models.Withdrawal))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["type", "user_id", "amount", "currency", "timestamp", "processed"])
    for d in dep_result.scalars().all():
        ts = d.created_at.isoformat() if isinstance(d.created_at, datetime) else ""
        writer.writerow(["deposit", d.user_id, d.amount, d.currency, ts, ""])
    for w in with_result.scalars().all():
        ts = w.requested_at.isoformat() if isinstance(w.requested_at, datetime) else ""
        writer.writerow(["withdrawal", w.user_id, w.amount, w.currency, ts, str(w.processed)])
    output.seek(0)
    headers = {"Content-Disposition": "attachment; filename=transactions.csv"}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)
