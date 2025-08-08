from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select
import csv
import io

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
    return {"users": users_count, "deposits": deposits_sum}


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

