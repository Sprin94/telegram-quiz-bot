import asyncio
from datetime import time

from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    create_or_update_schedule
)
from services.create_poll import _create_poll, _wrapper_for_create_poll

from filters.admin_user import IsAdmin
from cache import schedule_cache

router: Router = Router(name="admin-group")


@router.message(Command(commands=['set_time']))
async def set_time_for_poll(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    command: CommandObject,
):
    error_msg = 'Пожалуйста, укажите время проведения викторины.\nПример /set_time 15:15'
    if not command.args or ':' not in command.args or len(command.args.split(':')) != 2:
        return await message.answer(error_msg)
    args = command.args.split(':')
    try:
        poll_hour = int(args[0])
        poll_minute = int(args[1])
    except ValueError:
        return await message.answer(error_msg)
    await create_or_update_schedule(
        session=session,
        time=time(poll_hour, poll_minute),
        chat_id=message.chat.id,
    )
    if task := schedule_cache.pop(message.chat.id, None):
        task.cancel()
    task = asyncio.create_task(_wrapper_for_create_poll(bot, message.chat.id))
    schedule_cache[message.chat.id] = task
    await message.answer('Время проведения викторины установлено.\n')


@router.message(
        Command(commands=['poll']),
        F.chat.type.in_(["group", "supergroup"]),
        IsAdmin(),
)
async def create_poll_command(message: Message, bot: Bot):
    await _create_poll(bot=bot, chat_id=message.chat.id)


@router.message(
        Command(commands=['manage_quiz']),
        F.chat.type.in_(["group", "supergroup"]),
        IsAdmin(),
)
async def settings_chat(message: Message, bot: Bot, state: FSMContext):
    await bot.send_message(
        message.from_user.id,
        'Для выбора чата и создания вопросов для него используйте:\n'
        f'<code>/manage {message.chat.id}\n</code>',
        parse_mode='HTML'
    )
