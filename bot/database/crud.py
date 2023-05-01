from datetime import time

from aiogram.types import Chat as AiogramChat, Message, PollAnswer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func, update
from sqlalchemy.orm import joinedload

from database.schemas import QuestionSchema, AnswerSchema
from database.models import Chat, Question, Answer, Schedule, FinishedQuizzes


async def get_or_create_chat(session: AsyncSession, chat: AiogramChat):
    try:
        new_chat = Chat(id=chat.id, name=chat.title)
        session.add(new_chat)
        await session.commit()
        await session.refresh(new_chat)
    except IntegrityError:
        pass
    return new_chat


async def _create_question(session: AsyncSession,
                           question: QuestionSchema,) -> int:
    new_question = Question(**question.dict(exclude_none=True))
    session.add(new_question)
    await session.commit()
    await session.refresh(new_question)
    return new_question.id


async def _create_answers(
        session: AsyncSession,
        question_id: int,
        answers: list[AnswerSchema],
) -> None:
    for answer in answers:
        answer.question_id = question_id
        new_answer = Answer(**answer.dict(exclude_none=True))
        session.add(new_answer)
    await session.commit()


async def create_question_with_answers(
        session: AsyncSession,
        question: QuestionSchema,
        answers: list[AnswerSchema],
):
    question_id = await _create_question(session, question)
    await _create_answers(session, question_id, answers)


async def get_question_with_answers(session: AsyncSession, question_id) -> Question:
    stmt = (select(Question)
            .where(Question.id == question_id)
            .options(joinedload(Question.answers))
            )
    result = await session.execute(stmt)
    return result.scalar()


async def get_random_quiz(session: AsyncSession, chat_id: int) -> Question:
    stmt = (select(Question)
            .where(Question.chat_id == chat_id)
            .options(joinedload(Question.answers))
            .order_by(func.random())
            .limit(1)
            )
    result = await session.execute(stmt)
    return result.scalar()


async def get_questions_by_chat_id(session: AsyncSession, chat_id: int):
    stmt = (select(Question)
            .where(Question.chat_id == chat_id)
            .options(joinedload(Question.answers))
            )
    result = await session.execute(stmt)
    return result.unique().scalars().all()


async def delete_question(session: AsyncSession, question_id: int):
    question = await session.get(Question, question_id)
    if question:
        await session.delete(question)
        await session.commit()
        return True
    return None


async def create_or_update_schedule(session: AsyncSession, time: time, chat_id: int):
    new_schedule = Schedule(
        chat_id=chat_id,
        time=time
    )
    try:
        session.add(new_schedule)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        stmt = update(Schedule).where(Schedule.chat_id == chat_id).values(time=time)
        await session.execute(stmt)
        await session.commit()


async def get_schedule_time(session: AsyncSession, chat_id: int):
    stmt = select(Schedule.time).where(Schedule.chat_id == chat_id)
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_chat_id_schedules(session: AsyncSession):
    stmt = select(Schedule.chat_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def create_finished_quizzes(
    session: AsyncSession,
    poll_message: Message,
    question: Question
):
    quiz = FinishedQuizzes(
        chat_id=poll_message.chat.id,
        question_id=question.id,
        poll_id=poll_message.poll.id
    )
    session.add(quiz)
    await session.commit()


async def set_winner_finished_quizzes(
    session: AsyncSession,
    poll_answer: PollAnswer
):
    stmt = (update(FinishedQuizzes)
            .where(FinishedQuizzes.poll_id == poll_answer.poll_id)
            .values(winner=poll_answer.user.id))
    await session.execute(stmt)
    await session.commit()
