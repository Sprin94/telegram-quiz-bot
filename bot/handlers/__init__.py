from aiogram import Router


def setup_routers() -> Router:
    from . import (
        common, add_or_migrate, admin_changes_in_group, callbacks, poll,
        admin_handlers_in_group, admin_handlers_private_chat
    )
    router = Router()
    router.include_router(poll.router)
    router.include_router(admin_changes_in_group.router)
    router.include_router(admin_handlers_private_chat.router)
    router.include_router(common.router)
    router.include_router(admin_handlers_in_group.router)
    router.include_router(add_or_migrate.router)
    router.include_router(callbacks.router)
    return router
