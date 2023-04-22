from aiogram import Router


def setup_routers() -> Router:
    from . import admin_handlers, common, add_or_migrate
    router = Router()
    router.include_router(common.router)
    router.include_router(admin_handlers.router)
    router.include_router(add_or_migrate.router)
    return router
