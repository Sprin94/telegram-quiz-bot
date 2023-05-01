
from aiogram import Router, Bot
from aiogram.types import PollAnswer
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    set_winner_finished_quizzes
)

from cache import quiz_cache

router: Router = Router(name='poll')


@router.poll_answer()
async def poll_answer(poll_answer: PollAnswer, bot: Bot, session: AsyncSession):
    poll_correct_answer = quiz_cache.get(poll_answer.poll_id)
    if poll_correct_answer:
        if poll_correct_answer['correct_answer'] == poll_answer.option_ids[0]:
            data = quiz_cache.pop(poll_answer.poll_id)
            await bot.stop_poll(data['chat_id'], data['poll_message_id'])
            await bot.send_message(
                chat_id=data['chat_id'],
                text=(f'@{poll_answer.user.username} первый ответил правильно'),
            )
            await set_winner_finished_quizzes(session=session, poll_answer=poll_answer)
