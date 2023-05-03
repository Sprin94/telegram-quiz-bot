import asyncio
from datetime import datetime, timedelta

from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import create_schedule, get_schedules_by_chat_id, del_schedule
from services.create_poll import _create_poll, _wrapper_for_create_poll
from bot_responses import commands_response as text
from filters.admin_user import IsAdmin

router: Router = Router(name="admin-group")
router.message.filter(F.chat.type.in_(["group", "supergroup"]), IsAdmin())


@router.message(Command(commands=['add_time']))
async def add_time_for_poll(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    command: CommandObject,
):
    try:
        times = command.args or ''
        poll_time = datetime.strptime(times, '%H:%M').time()
    except ValueError:
        return await message.answer(text.ERROR_MESSAGE_ADD_TIME)
    schedule = await create_schedule(
        session=session,
        time=poll_time,
        chat_id=message.chat.id,
    )
    if schedule:
        in_5_min = (datetime.now() + timedelta(minutes=5)).time()
        if in_5_min > schedule.time:
            asyncio.create_task(_wrapper_for_create_poll(bot, schedule))
        return await message.answer(f'Новое время викторины добавлено.\n{poll_time}')
    return await message.answer('Викторина в это время уже проводится.')


@router.message(Command(commands=['poll']))
async def create_poll_command(message: Message, bot: Bot):
    await _create_poll(bot=bot, chat_id=message.chat.id)


@router.message(Command(commands=['quiz_times']))
async def get_quiz_times(message: Message, session: AsyncSession):
    schedules = await get_schedules_by_chat_id(session, message.chat.id)
    res = '\n'.join(f'{i}. {q.time}' for i, q in enumerate(schedules, start=1))
    await message.answer(f'Для удаления используйте /del_time HH:MM\n{res}')


@router.message(Command(commands=['del_time']))
async def del_time_quiz(message: Message, session: AsyncSession, command: CommandObject):

    try:
        times = command.args or ''
        poll_time = datetime.strptime(times, '%H:%M').time()
    except ValueError:
        return await message.answer(text.ERROR_MESSAGE_DEL_TIME)
    is_del = await del_schedule(session, poll_time, message.chat.id)
    if is_del:
        return await message.answer('Время викторины удалено.')
    return await message.answer('Время викторины не найдено.')
