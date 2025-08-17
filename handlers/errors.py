# handlers/errors.py
import logging
from typing import Optional

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ErrorEvent, Update

from utils.i18n import t

# Экспортируем именно errors_router — под это имя идёт импорт в handlers/__init__.py
errors_router = Router(name="errors")

# Алиас для обратной совместимости (если где-то импортировали `router`)
router = errors_router

__all__ = ["errors_router", "router"]


def _detect_lang(update: Update) -> str:
    """
    Определяем язык пользователя (только ru/en). Фолбэк — en.
    """
    code: Optional[str] = None
    if update.message and update.message.from_user:
        code = update.message.from_user.language_code
    elif update.callback_query and update.callback_query.from_user:
        code = update.callback_query.from_user.language_code

    if not code:
        return "en"
    code = code.lower()
    return code if code in ("ru", "en") else "en"


@errors_router.errors()
async def global_error_handler(event: ErrorEvent) -> bool:
    """
    Глобальный обработчик ошибок aiogram v3.
    Показывает пользователю безопасное сообщение и глотает исключение.
    """
    update = event.update
    exception = event.exception

    try:
        lang = _detect_lang(update)
        text = t(lang, "fallback_error")

        if update.message:
            await update.message.answer(text)
        elif update.callback_query:
            await update.callback_query.answer(text, show_alert=True)

    except TelegramBadRequest:
        # Игнорируем ошибки доставки fallback-сообщения (например, "message is not modified")
        pass
    except Exception:
        # Любые другие ошибки при отправке fallback — просто логируем
        logging.exception("Failed to send fallback message")

    # Логируем исходное исключение
    logging.exception("Unhandled exception in update processing: %s", exception)

    # True — предотвращает повторный рейз исключения
    return True
