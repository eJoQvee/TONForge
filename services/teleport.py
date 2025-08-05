import httpx
from bot_config import settings
from database import models

TELEPORT_API_URL = settings.teleport_api_url

async def generate_short_link(invite: models.Invite) -> str:
    """Generate a short link for an invite using the Teleport service.

    The invite's ``external_url`` is sent to the Teleport API, the returned
    short link is stored in the invite and also returned.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(TELEPORT_API_URL, json={"url": invite.external_url})
        resp.raise_for_status()
        data = resp.json()

    short_link = data.get("short") or data.get("short_link") or data.get("url")
    invite.short_link = short_link
    invite.is_active = True
    return short_link
