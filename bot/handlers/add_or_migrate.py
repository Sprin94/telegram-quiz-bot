from asyncio import sleep

from aiogram import Bot, Router, types, F
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION
from sqlalchemy.ext.asyncio import AsyncSession

from migration_cache import cache
from database.crud import get_or_create_chat

router: Router = Router()
chats_variants = {'group': 'группу', 'supergroup': 'супергруппу'}


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION),
                       F.chat.type.in_({'group', 'supergroup'}))
async def bot_added_to_group(
    event: types.ChatMemberUpdated,
    bot: Bot,
    session: AsyncSession,
):
    await sleep(1.0)
    if event.chat.id not in cache.keys():
        await bot.send_message(
            chat_id=event.chat.id,
            text=f'Бот добавлен в {chats_variants[event.chat.type]}\n'
                 f'chat ID: {event.chat.id}'
        )
        await get_or_create_chat(session=session, chat=event.chat)


@router.message(F.migrate_to_chat_id)
async def group_to_supegroup_migration(message: types.Message, bot: Bot):
    await bot.send_message(
        message.migrate_to_chat_id,
        f'Группа повышена до супергруппы.\n'
        f'Старый ID: {message.chat.id}\n'
        f'Новый ID: {message.migrate_to_chat_id}'
    )
    cache[message.migrate_to_chat_id] = True
