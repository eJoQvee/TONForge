from __future__ import annotations

import asyncio
import sys
from importlib import import_module
from typing import Sequence

from sqlalchemy import inspect, text

from database.db import engine, Base as DbBase, DATABASE_URL, ENV


def _import_models() -> "list[object]":
    modules: list[object] = []
    candidates: Sequence[str] = (
        "database.models",
        "database.models.user",
        "database.models.deposit",
        "database.models.withdrawal",
        "database.models.transaction",
        "database.models.referral",
        "database.models.config",
    )
    for mod in candidates:
        try:
            m = import_module(mod)
            modules.append(m)
        except ModuleNotFoundError:
            continue
        except Exception as e:
            print(f"[MIGRATE] warn: import {mod!r} failed: {e}", file=sys.stderr)
    return modules


async def migrate() -> None:
    print(f"[MIGRATE] ENV={ENV}")
    print(f"[MIGRATE] DATABASE_URL={DATABASE_URL!r}")

    modules = _import_models()

    # Собираем все metadata (на случай, если где-то другой Base)
    metadatas = {DbBase.metadata}
    for m in modules:
        model_base = getattr(m, "Base", None)
        if model_base is not None and getattr(model_base, "metadata", None) is not None:
            if model_base is not DbBase:
                metadatas.add(model_base.metadata)

    for md in metadatas:
        print(f"[MIGRATE] metadata tables before: {sorted(md.tables.keys())}")

    async with engine.begin() as conn:
        # 1) Создаём недостающие таблицы
        for md in metadatas:
            await conn.run_sync(md.create_all)

        # helpers
        def _table_exists(sync_conn, table: str) -> bool:
            insp = inspect(sync_conn)
            return table in insp.get_table_names()

        def _has_column(sync_conn, table: str, col: str) -> bool:
            insp = inspect(sync_conn)
            try:
                cols = [c["name"] for c in insp.get_columns(table)]
            except Exception:
                return False
            return col in cols

        # users: добавочные поля
        if await conn.run_sync(_table_exists, "users"):
            if not await conn.run_sync(_has_column, "users", "is_blocked"):
                print("[MIGRATE] add column users.is_blocked ...")
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE")
                )
            if not await conn.run_sync(_has_column, "users", "last_ip"):
                print("[MIGRATE] add column users.last_ip ...")
                await conn.execute(text("ALTER TABLE users ADD COLUMN last_ip VARCHAR"))
        else:
            print("[MIGRATE] warn: table 'users' not found after create_all().", file=sys.stderr)

        # settings: дефолтная строка
        if await conn.run_sync(_table_exists, "settings"):
            cnt = await conn.scalar(text("SELECT COUNT(*) FROM settings WHERE id=1"))
            if not cnt:
                print("[MIGRATE] insert default settings row (id=1) ...")
                await conn.execute(
                    text(
                        "INSERT INTO settings "
                        "(id, daily_percent, min_deposit, min_withdraw, withdraw_delay_hours, notification_text) "
                        "VALUES (1, 0.023, 10, 50, 24, '')"
                    )
                )
        else:
            print("[MIGRATE] warn: table 'settings' not found after create_all().", file=sys.stderr)

        # deposits: добавляем недостающие поля
        if await conn.run_sync(_table_exists, "deposits"):
            if not await conn.run_sync(_has_column, "deposits", "address"):
                print("[MIGRATE] add column deposits.address ...")
                await conn.execute(text("ALTER TABLE deposits ADD COLUMN address VARCHAR"))
            if not await conn.run_sync(_has_column, "deposits", "is_active"):
                print("[MIGRATE] add column deposits.is_active ...")
                await conn.execute(
                    text("ALTER TABLE deposits ADD COLUMN is_active BOOLEAN DEFAULT FALSE")
                )
        else:
            print("[MIGRATE] warn: table 'deposits' not found after create_all().", file=sys.stderr)

        # transactions: по возможности обеспечим уникальность tx_hash
        if await conn.run_sync(_table_exists, "transactions"):
            try:
                # Postgres: добавим constraint, если его нет
                await conn.execute(
                    text(
                        "ALTER TABLE transactions "
                        "ADD CONSTRAINT IF NOT EXISTS uq_transactions_tx_hash UNIQUE (tx_hash)"
                    )
                )
            except Exception:
                # На SQLite ALTER TABLE ограничен — просто молча пропустим
                pass

    print("[MIGRATE] Done.")


if __name__ == "__main__":
    asyncio.run(migrate())
