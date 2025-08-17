from aiogram import Router
from .errors import errors_router
# from .start import start_router
# ...

router = Router()
router.include_router(errors_router)
# router.include_router(start_router)
# ...
