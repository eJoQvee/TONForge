from aiogram import Router
from aiogram.types import Update
from aiogram.exceptions import TelegramBadRequest
import logging
from utils.i18n import t

router = Router()

@router.errors()
async def global_error_handler(update: Update, exception: Exception) -> bool:
    """Send fallback message to user on unexpected errors."""
    try:
        if update.message:
            lang = update.message.from_user.language_code or "en"
            lang = lang if lang in ("ru", "en") else "en"
            await update.message.answer(t(lang, "fallback_error"))
        elif update.callback_query:
            lang = update.callback_query.from_user.language_code or "en"
            lang = lang if lang in ("ru", "en") else "en"
            await update.callback_query.answer(t(lang, "fallback_error"), show_alert=True)
    except TelegramBadRequest:
        pass
    logging.exception("Unhandled exception: %s", exception)
    return True
