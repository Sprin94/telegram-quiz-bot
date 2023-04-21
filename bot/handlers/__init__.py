from aiogram import Router


def setup_routers() -> Router:
    from . import admin_handlers, common
    router = Router()
    router.include_router(common.router)
    router.include_router(admin_handlers.router)
    return router
