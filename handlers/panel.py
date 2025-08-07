from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot_config import settings
from utils.i18n import t

router = Router()


@router.message(Command("panel123"))
async def cmd_panel(message: Message) -> None:
    """Send admin panel link to authorized users."""
    if settings.admin_ids and message.from_user.id not in settings.admin_ids:
        await message.answer("Access denied")
        return
    if not settings.base_webapp_url:
        await message.answer("Admin panel URL is not configured")
        return
    lang = message.from_user.language_code or "en"
    lang = lang if lang in ("ru", "en") else "en"
    url = f"{settings.base_webapp_url}/admin"
    await message.answer(t(lang, "admin_panel", url=url))
