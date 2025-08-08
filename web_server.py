import asyncio
import logging
import os
from aiohttp import web

logger = logging.getLogger(__name__)


async def handle(_request: web.Request) -> web.Response:
    """Simple health endpoint for Render."""
    return web.Response(text="OK")


async def main() -> None:
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ["PORT"])
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Web server started on port %s", port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
