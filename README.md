# TONForge

Telegram-based investment bot MVP.

## Setup

1. Copy `.env.example` to `.env` and fill in required values.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
   This installs packages such as `aiogram`, which is required to run the bot.
3. Initialize the database tables:

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
4. Start the bot:

   ```bash
   python main.py
   ```

Running `python main.py` requires network access to Telegram servers.
