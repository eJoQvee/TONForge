# TONForge

Telegram-based investment bot MVP.

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

2. Copy `.env.example` to `.env` and fill in required values. The `TELEPORT_API_URL`
   is available in the Teleport dashboard: https://teleport.org/dashboard.
3. Start PostgreSQL and Redis using Docker:

   ```bash
   docker-compose up -d
   ```

   Verify connections:

   ```bash
   docker-compose exec postgres pg_isready -U $POSTGRES_USER
   docker-compose exec redis redis-cli ping
   ```

4. Initialize the database tables:

   ```bash
   python - <<'PY'
import asyncio
from database.db import engine
from database import models

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

asyncio.run(main())
PY
   ```
5. Start the bot:

   ```bash
   python main.py
   ```

Running `python main.py` requires network access to Telegram servers.
