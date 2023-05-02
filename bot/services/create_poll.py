import asyncio
from datetime import timedelta, datetime
from random import shuffle

from aiogram import Bot

from database.db import sessionmaker
from database.models import Schedule
from cache import quiz_cache
from database.crud import (
    get_schedules_in_5_minutes, get_schedule_by_time_and_chat_id, get_random_quiz,
    create_finished_quizzes
)


async def create_quizzes_tasks(bot: Bot):
    while True:
        async with sessionmaker() as session:
            now = datetime.now().time()
            in_5_min = (datetime.now() + timedelta(minutes=5)).time()
            schedules = await get_schedules_in_5_minutes(
                session=session,
                cleft=now,
                cright=in_5_min,
            )
            for schedule in schedules:
                asyncio.create_task(_wrapper_for_create_poll(
                    bot=bot,
                    schedule=schedule)
                )
            await asyncio.sleep(300)


async def _wrapper_for_create_poll(bot: Bot, schedule: Schedule):
    time_now = datetime.now()
    poll_time = time_now.combine(time_now, schedule.time)
    delta = poll_time - time_now
    await asyncio.sleep(delta.seconds)
    async with sessionmaker() as session:
        if not await get_schedule_by_time_and_chat_id(
            session,
            schedule.chat_id,
            schedule.time
        ):
            return
    await _create_poll(bot=bot, chat_id=schedule.chat_id)


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
