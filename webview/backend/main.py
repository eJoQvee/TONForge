# webview/backend/main.py
from __future__ import annotations

import json
import os
from urllib.parse import parse_qsl

from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import session_generator as get_session
from database import models
from utils.referrals import get_referral_stats
from utils.antifraud import check_and_update_ip
from services import deposit as deposit_service
from admin.panel import router as admin_router
from bot_config import settings

app = FastAPI(title="TONForge Web", version="1.0.0")

ALLOWED_ORIGINS = [
    os.getenv("BASE_WEBAPP_URL", "https://tonforge-web.onrender.com"),
    "https://t.me",
    "https://web.telegram.org",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict:
    return {"ok": True}

# ---------- Встроенный фронт (отдаём по /app) ----------
INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>TONForge WebApp</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root { color-scheme: light dark; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 16px;
           color: var(--tg-theme-text-color,#111); background: var(--tg-theme-bg-color,#fff); }
    .card { border: 1px solid #2c2c2c22; border-radius: 14px; padding: 16px; margin-bottom: 16px;
            background: var(--tg-theme-secondary-bg-color,#fff); }
    input, select, button { padding: 12px; border-radius: 12px; border: 1px solid #3d3d3d33; background: transparent; color: inherit; }
    button { cursor: pointer; }
    .row { display: flex; gap: 10px; align-items: center; }
    .row > * { flex: 1; }
    .muted { opacity: .75; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Courier New", monospace; }
    .err { color: #ef4444; white-space: pre-wrap; }
    h2 { margin: 8px 0 16px; font-size: 28px; }
    h3 { margin: 0 0 10px; font-size: 20px; }
  </style>
</head>
<body>
  <h2>TONForge</h2>

  <div class="card" id="profile">
    <div class="muted">Loading profile…</div>
  </div>

  <div class="card">
    <h3>New deposit</h3>
    <div class="row" style="margin: 8px 0">
      <input id="amount" type="number" placeholder="Amount" min="0" step="0.0000001" value="10"/>
      <select id="currency">
        <option value="TON">TON</option>
        <option value="USDT">USDT</option>
      </select>
    </div>
    <button id="btnCreate">Create deposit</button>
    <div id="depositResult" class="muted" style="margin-top:8px"></div>
  </div>

  <script>
    const tg = window.Telegram?.WebApp;
    tg?.ready?.(); tg?.expand?.();

    // Получаем userId из Telegram, а если его нет — оставим null (есть фолбэк по ?user_id=)
    const initDataStr = tg?.initData || "";
    const userId = tg?.initDataUnsafe?.user?.id || null;

    async function api(path, opts = {}) {
      // добавляем ?user_id= для надёжности (Telegram иногда не кладёт заголовок в iOS)
      const url = new URL(path, window.location.origin);
      if (userId) url.searchParams.set("user_id", String(userId));

      const headers = Object.assign({"X-Telegram-Init-Data": initDataStr}, opts.headers || {});
      const res = await fetch(url.toString(), Object.assign({}, opts, { headers }));
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || res.statusText);
      }
      return res.json();
    }

    async function loadProfile() {
      const box = document.getElementById("profile");
      try {
        const me = await api("/api/me");
        box.innerHTML = `
          <div><b>Telegram ID:</b> <span class="mono">${me.telegram_id}</span></div>
          <div><b>Balances:</b> TON ${me.balance_ton} / USDT ${me.balance_usdt}</div>
          <div><b>Daily %:</b> ${me.daily_percent}</div>
          <div><b>Min deposit:</b> ${me.min_deposit} | <b>Min withdraw:</b> ${me.min_withdraw}</div>
          <div><b>Referral link:</b> ${me.referral_link ? `<a href="${me.referral_link}">${me.referral_link}</a>` : '<span class="muted">N/A</span>'}</div>
          <div><b>TON wallet:</b> <span class="mono">${me.ton_wallet || 'N/A'}</span></div>
          <div><b>USDT wallet:</b> <span class="mono">${me.usdt_wallet || 'N/A'}</span></div>
        `;
      } catch (e) {
        box.innerHTML = `<div class="err">Error: ${e.message}</div>`;
      }
    }

    document.getElementById("btnCreate").addEventListener("click", async () => {
      const amount = parseFloat(document.getElementById("amount").value || "0");
      const currency = document.getElementById("currency").value;
      const out = document.getElementById("depositResult");
      out.textContent = "Processing…";
      try {
        const data = await api("/api/deposits", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({ amount, currency })
        });
        out.innerHTML = `
          ✅ Created. Send <b>${data.amount} ${data.currency}</b> to<br/>
          <span class="mono">${data.address}</span><br/>
          with label/memo: <span class="mono">${data.label}</span>
        `;
      } catch (e) {
        out.innerHTML = `<span class="err">Error: ${e.message}</span>`;
      }
    });

    loadProfile();
  </script>
</body>
</html>
"""

# отдаём фронт как HTML с принудительными заголовками
@app.get("/app", include_in_schema=False, response_class=HTMLResponse)
async def app_index() -> HTMLResponse:
    return HTMLResponse(
        content=INDEX_HTML,
        media_type="text/html; charset=utf-8",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )

# корень перенаправляем на /app, чтобы обойти возможный кэш/старый MIME
@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/app", status_code=302)

# ---------- API ----------
router = APIRouter(prefix="/api")

def _extract_telegram_id_from_init_data(request: Request) -> int | None:
    raw = request.headers.get("X-Telegram-Init-Data") or ""
    if not raw:
        return None
    try:
        data = dict(parse_qsl(raw, keep_blank_values=True))
        if "user" in data:
            u = json.loads(data["user"])
            tid = u.get("id")
            if isinstance(tid, int):
                return tid
    except Exception:
        return None
    return None

async def _get_or_create_user(session: AsyncSession, telegram_id: int, ip: str | None = None) -> models.User:
    res = await session.execute(select(models.User).where(models.User.telegram_id == telegram_id))
    user = res.scalar_one_or_none()
    if not user:
        user = models.User(telegram_id=telegram_id, language="en")
        session.add(user)
        await session.commit()
        await session.refresh(user)
    if ip:
        await check_and_update_ip(session, user, ip)
    if getattr(user, "is_blocked", False):
        raise HTTPException(status_code=403, detail="user_blocked")
    return user

def _bot_username() -> str:
    return getattr(settings, "bot_username", None) or os.getenv("BOT_USERNAME", "TONForge1_bot")

@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}

class DepositCreateIn(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str  # "TON" | "USDT"

@router.get("/me")
async def me(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    telegram_id = _extract_telegram_id_from_init_data(request)
    if telegram_id is None:
        q_user = request.query_params.get("user_id")
        if q_user and q_user.isdigit():
            telegram_id = int(q_user)
    if telegram_id is None:
        raise HTTPException(status_code=401, detail="no_telegram_context")

    user = await _get_or_create_user(session, telegram_id, request.client.host if request.client else None)

    cfg = await session.get(models.Config, 1)
    daily_percent = float(cfg.daily_percent if cfg else 0.023)
    min_deposit   = float(cfg.min_deposit if cfg else 10.0)
    min_withdraw  = float(cfg.min_withdraw if cfg else 50.0)

    ref_link = f"https://t.me/{_bot_username()}?start={user.telegram_id}"

    return {
        "telegram_id": user.telegram_id,
        "balance_ton": float(user.balance_ton or 0),
        "balance_usdt": float(user.balance_usdt or 0),
        "daily_percent": daily_percent,
        "min_deposit": min_deposit,
        "min_withdraw": min_withdraw,
        "referral_link": ref_link,
        "ton_wallet": getattr(settings, "ton_wallet", None),
        "usdt_wallet": getattr(settings, "usdt_wallet", None),
    }

@router.post("/deposits")
async def create_deposit_endpoint(
    data: DepositCreateIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        telegram_id = _extract_telegram_id_from_init_data(request)
        if telegram_id is None:
            q_user = request.query_params.get("user_id")
            if q_user and q_user.isdigit():
                telegram_id = int(q_user)
        if telegram_id is None:
            raise HTTPException(status_code=401, detail="no_telegram_context")

        user = await _get_or_create_user(session, telegram_id, request.client.host if request.client else None)

        cfg = await session.get(models.Config, 1)
        min_dep = float(cfg.min_deposit if cfg else 10.0)
        amount = float(data.amount)
        currency = data.currency.upper()
        if currency not in {"TON", "USDT"}:
            raise HTTPException(status_code=400, detail="currency_must_be_TON_or_USDT")
        if amount < min_dep:
            raise HTTPException(status_code=400, detail=f"min_deposit_is_{min_dep}")

        address = settings.ton_wallet if currency == "TON" else settings.usdt_wallet
        if not address:
            raise HTTPException(status_code=500, detail=f"{currency}_address_not_configured")

        dep = await deposit_service.create_deposit(
            session,
            user_id=user.id,
            amount=amount,
            currency=currency,
            address=None if currency == "TON" else address,
        )

        return {"id": dep.id, "amount": amount, "currency": currency, "address": address, "label": str(dep.id)}
    except HTTPException:
        raise
    except Exception as e:
        import traceback, sys
        print("[/api/deposits] error:", e, file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/referrals")
async def referrals(
    user_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> dict:
    user = await _get_or_create_user(session, user_id, request.client.host if request.client else None)
    stats = await get_referral_stats(session, user.id)
    link = f"https://t.me/{_bot_username()}?start={user_id}"
    earned = stats["bonus_ton"] + stats["bonus_usdt"]
    return {"link": link, "count": stats["invited"], "earned": earned}

@router.get("/profile/{telegram_id}")
async def get_profile(
    telegram_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> dict:
    user = await _get_or_create_user(session, telegram_id, request.client.host if request.client else None)
    stats = await get_referral_stats(session, user.id)
    return {"telegram_id": user.telegram_id, "balance_ton": user.balance_ton, "balance_usdt": user.balance_usdt, "referrals": stats}

@router.get("/operations")
async def operations(
    user_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> dict:
    user = await _get_or_create_user(session, user_id, request.client.host if request.client else None)
    deposits = await session.execute(
        select(models.Deposit.amount, models.Deposit.currency, models.Deposit.created_at)
        .where(models.Deposit.user_id == user.id)
    )
    withdrawals = await session.execute(
        select(models.Withdrawal.amount, models.Withdrawal.currency, models.Withdrawal.requested_at, models.Withdrawal.processed)
        .where(models.Withdrawal.user_id == user.id)
    )
    return {
        "deposits": [
            {"amount": a, "currency": c, "created_at": (dt.isoformat() if dt else None)}
            for a, c, dt in deposits.all()
        ],
        "withdrawals": [
            {"amount": a, "currency": c, "requested_at": (dt.isoformat() if dt else None), "processed": p}
            for a, c, dt, p in withdrawals.all()
        ],
    }

app.include_router(router)
app.include_router(admin_router)
