import asyncio
from datetime import timedelta, datetime
from random import shuffle

from aiogram import Bot

from database.db import sessionmaker
from cache import quiz_cache, schedule_cache
from database.crud import (
    get_chat_id_schedules, get_schedule_time, get_random_quiz, create_finished_quizzes

)


async def create_quizzes_tasks(bot: Bot):
    async with sessionmaker() as session:
        chats_id = await get_chat_id_schedules(session)
        for chat_id in chats_id:
            task = asyncio.create_task(_wrapper_for_create_poll(bot=bot, chat_id=chat_id))
            quiz_cache[chat_id] = task


async def _wrapper_for_create_poll(bot: Bot, chat_id: int):
    async with sessionmaker() as session:
        schedule_time = await get_schedule_time(session=session, chat_id=chat_id)
    time_now = datetime.now()
    poll_time = time_now.combine(time_now, schedule_time)
    delta = poll_time - time_now
    if delta.days < 0:
        poll_time = poll_time + timedelta(days=1)
        delta = poll_time - time_now
    await asyncio.sleep(delta.seconds)
    await _create_poll(bot=bot, chat_id=chat_id)
    task = asyncio.create_task(_wrapper_for_create_poll(bot, chat_id))
    schedule_cache[chat_id] = task


async def _create_poll(bot: Bot, chat_id: int):
    async with sessionmaker() as session:
        quiz = await get_random_quiz(session=session, chat_id=chat_id)
        if not quiz:
            return await bot.send_message(chat_id, 'Не найдены вопросы для этого чата.')
        shuffle(quiz.answers)
        answers = []
        for i, answer in enumerate(quiz.answers):
            answers.append(answer.text)
            if answer.is_right:
                correct_option_id = i
        poll_message = await bot.send_poll(
            chat_id=chat_id,
            question=quiz.text,
            type='quiz',
            correct_option_id=correct_option_id,
            options=answers,
            is_anonymous=False,
            close_date=timedelta(minutes=1)
        )
        quiz_cache[poll_message.poll.id] = {
            'chat_id': chat_id,
            'correct_answer': correct_option_id,
            'poll_message_id': poll_message.message_id
        }
        await create_finished_quizzes(
            session=session,
            poll_message=poll_message,
            question=quiz
        )
