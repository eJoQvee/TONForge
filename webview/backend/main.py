from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database.db import get_session
from database import models

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # настройте под домен
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/profile/{telegram_id}")
async def get_profile(telegram_id: int, session=Depends(get_session)):
    user = await session.get(models.User, telegram_id)
    if not user:
        return {"error": "user_not_found"}
    return {
        "telegram_id": user.telegram_id,
        "balance_ton": user.balance_ton,
        "balance_usdt": user.balance_usdt
    }
