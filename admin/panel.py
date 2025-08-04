from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
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
