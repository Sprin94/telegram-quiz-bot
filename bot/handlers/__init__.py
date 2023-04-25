from aiogram import Router


def setup_routers() -> Router:
    from . import (
        admin_handlers, common, add_or_migrate, admin_changes_in_group, callbacks
    )
    router = Router()
    router.include_router(admin_changes_in_group.router)
    router.include_router(common.router)
    router.include_router(admin_handlers.router)
    router.include_router(add_or_migrate.router)
    router.include_router(callbacks.router)
    return router
