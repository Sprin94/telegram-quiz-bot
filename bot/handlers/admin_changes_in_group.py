from aiogram import Router, Bot
from aiogram.filters.chat_member_updated import (
    ChatMemberUpdatedFilter, KICKED, LEFT, RESTRICTED, MEMBER, ADMINISTRATOR, CREATOR
)
from aiogram.types import ChatMemberUpdated

from cache import admin_cache
from services.utils import get_admins_id_set


router = Router()


@router.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(
            (KICKED | LEFT | RESTRICTED | MEMBER)
            >>
            (ADMINISTRATOR | CREATOR)
        )
    )
)
async def admin_promoted(event: ChatMemberUpdated, bot: Bot):
    if not admin_cache.get(event.chat.id):
        admin_cache[event.chat.id] = await get_admins_id_set(
            chat_id=event.chat.id,
            bot=bot
        )
    admin_cache[event.chat.id].add(event.new_chat_member.user.id)


@router.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(
            (KICKED | LEFT | RESTRICTED | MEMBER)
            <<
            (ADMINISTRATOR | CREATOR)
        )
    )
)
async def admin_demoted(event: ChatMemberUpdated, bot: Bot):
    if not admin_cache.get(event.chat.id):
        admin_cache[event.chat.id] = await get_admins_id_set(
            chat_id=event.chat.id,
            bot=bot
        )
    admin_cache[event.chat.id].discard(event.new_chat_member.user.id)
