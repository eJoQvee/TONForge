# handlers/__init__.py
from aiogram import Router

# Подключаем только подмодули, которые экспортируют <name>_router
# Важно: внутри подмодулей НЕЛЬЗЯ делать `from handlers import router`,
# чтобы не было циклических импортов.

from .errors import errors_router
# from .start import start_router
# from .profile import profile_router
# from .withdraw import withdraw_router
# ... добавляй по мере готовности

# Корневой роутер, который собирает все остальные
router = Router(name="root")

# Всегда сначала ошибки
router.include_router(errors_router)

# Примеры подключения других роутеров (раскомментируй, когда файлы будут готовы):
# router.include_router(start_router)
# router.include_router(profile_router)
# router.include_router(withdraw_router)

__all__ = ["router"]
