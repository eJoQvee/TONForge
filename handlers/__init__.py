# handlers/__init__.py
from aiogram import Router

# Подключаем только подмодули, которые экспортируют <name>_router
# Важно: внутри подмодулей НЕЛЬЗЯ делать `from handlers import router`,
# чтобы не было циклических импортов.

from .errors import errors_router
from .start import router as start_router
from .help import router as help_router
from .profile import router as profile_router
from .balance import router as balance_router
from .deposit import router as deposit_router
from .withdraw import router as withdraw_router
from .referral import router as referral_router
from .panel import router as panel_router

# Корневой роутер, который собирает все остальные
router = Router(name="root")

# Всегда сначала ошибки
router.include_router(errors_router)

# Подключаем остальные роутеры
router.include_router(start_router)
router.include_router(help_router)
router.include_router(profile_router)
router.include_router(balance_router)
router.include_router(deposit_router)
router.include_router(withdraw_router)
router.include_router(referral_router)
router.include_router(panel_router)

__all__ = ["router"]
