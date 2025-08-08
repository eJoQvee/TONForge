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
   Set `CHANNEL_ID` to enable channel notifications (optional).
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
      python database/migrate.py

   ```
5. Start the bot:

   ```bash
   python main.py
   ```

6. Run the WebView backend (FastAPI):

   ```bash
    uvicorn webview.backend.main:app --reload
    ```

7. Launch the WebView frontend (React):

    ```bash
    cd webview/frontend
    npm start
    ```

Running `python main.py` requires network access to Telegram servers.

## Tests

Install dependencies and run the test suite:

```bash
pip install -r requirements.txt
pytest
```
