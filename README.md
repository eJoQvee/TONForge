 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index e69de29bb2d1d6434b8b29ae775ad8c2e48c5391..0d788b7341408d88e5e7f194e13fc0797d386f20 100644
--- a/README.md
+++ b/README.md
@@ -0,0 +1,35 @@
+# TONForge
+
+Telegram-based investment bot MVP.
+
+## Setup
+
+1. Copy `.env.example` to `.env` and fill in required values.
+2. Install dependencies:
+
+   ```bash
+   pip install -r requirements.txt
+   ```
+   If you encounter `ModuleNotFoundError: No module named 'sqlalchemy'`, ensure this step completes successfully.
+3. Initialize the database tables:
+
+   ```bash
+   python - <<'PY'
+import asyncio
+from database.db import engine
+from database import models
+
+async def main():
+    async with engine.begin() as conn:
+        await conn.run_sync(models.Base.metadata.create_all)
+
+asyncio.run(main())
+PY
+   ```
+4. Start the bot:
+
+   ```bash
+   python main.py
+   ```
+
+Running `python main.py` requires network access to Telegram servers.
 
EOF
)