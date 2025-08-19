import asyncio
import sys
from importlib import import_module
from typing import Sequence

from sqlalchemy import inspect, text

from database.db import engine, Base as DbBase, DATABASE_URL, ENV


def _import_models() -> "list[object]":
    """
    Импортируем модули с моделями, чтобы они зарегистрировались в metadata.
    """
    modules: list[object] = []
    candidates: Sequence[str] = (
        "database.models",              # общий файл со всеми моделями
        # остальные — на случай, если где-то разнесёшь по модулям
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

    # Собираем все возможные metadata, на случай, если вдруг есть несколько Base
    metadatas = {DbBase.metadata}
    for m in modules:
        model_base = getattr(m, "Base", None)
        if model_base is not None and getattr(model_base, "metadata", None) is not None:
            if model_base is not DbBase:
                metadatas.add(model_base.metadata)

    # Диагностика: какие таблицы видим до create_all
    for md in metadatas:
        print(f"[MIGRATE] metadata tables before: {sorted(md.tables.keys())}")

    async with engine.begin() as conn:
        # 1) Создаём все таблицы для каждого metadata
        for md in metadatas:
            await conn.run_sync(md.create_all)

        # 2) Инспекция — проверим необходимые колонки/строки и дольём недостающее
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

        # --- users: ensure is_blocked / last_ip ---
        users_exist = await conn.run_sync(_table_exists, "users")
        if not users_exist:
            print("[MIGRATE] warn: table 'users' not found even after create_all().", file=sys.stderr)
        else:
            if not await conn.run_sync(_has_column, "users", "is_blocked"):
                print("[MIGRATE] add column users.is_blocked ...")
                await conn.execute(text(
                    "ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE"
                ))
            if not await conn.run_sync(_has_column, "users", "last_ip"):
                print("[MIGRATE] add column users.last_ip ...")
                await conn.execute(text(
                    "ALTER TABLE users ADD COLUMN last_ip VARCHAR"
                ))

        # --- deposits: ensure address ---
        deposits_exist = await conn.run_sync(_table_exists, "deposits")
        if deposits_exist and not await conn.run_sync(_has_column, "deposits", "address"):
            print("[MIGRATE] add column deposits.address ...")
            await conn.execute(text(
                "ALTER TABLE deposits ADD COLUMN address VARCHAR"
            ))

        # --- settings: ensure default row id=1 ---
        settings_exist = await conn.run_sync(_table_exists, "settings")
        if not settings_exist:
            print("[MIGRATE] warn: table 'settings' not found even after create_all().", file=sys.stderr)
        else:
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

    print("[MIGRATE] Done.")


if __name__ == "__main__":
    asyncio.run(migrate())
