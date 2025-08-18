from aiogram import Router

# --- errors: поддерживаем errors_router и router ---
try:
    from .errors import errors_router
except ImportError:
    from .errors import router as errors_router

# --- start ---
try:
    from .start import start_router
except ImportError:
    from .start import router as start_router

# --- help ---
try:
    from .help import help_router
except ImportError:
    from .help import router as help_router

# --- profile ---
try:
    from .profile import profile_router
except ImportError:
    from .profile import router as profile_router

# --- balance ---
try:
    from .balance import balance_router
except ImportError:
    from .balance import router as balance_router

# --- deposit ---
try:
    from .deposit import deposit_router
except ImportError:
    from .deposit import router as deposit_router

# --- withdraw ---
try:
    from .withdraw import withdraw_router
except ImportError:
    from .withdraw import router as withdraw_router

# --- referral ---
try:
    from .referral import referral_router
except ImportError:
    from .referral import router as referral_router

# --- panel ---
try:
    from .panel import panel_router
except ImportError:
    from .panel import router as panel_router

# Корневой агрегатор
router = Router(name="root")

# Всегда сначала ошибки
router.include_router(errors_router)

# Остальные роутеры
router.include_router(start_router)
router.include_router(help_router)
router.include_router(profile_router)
router.include_router(balance_router)
router.include_router(deposit_router)
router.include_router(withdraw_router)
router.include_router(referral_router)
router.include_router(panel_router)

__all__ = ["router"]
