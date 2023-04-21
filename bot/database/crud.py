from aiogram.types import Chat as AiogramChat
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from database.schemas import QuestionSchema, AnswerSchema
from database.models import Chat, Question, Answer


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


async def get_question_with_answers(session: AsyncSession, question_id: int):
    stmt = (select(Question)
            .where(id == question_id)
            .options(joinedload(Question.answers))
            )
    result = await session.execute(stmt)
    return result.unique().scalars().first()


async def get_random_quiz(session: AsyncSession, chat_id: int):
    stmt = (select(Question)
            .where(chat_id == chat_id)
            .options(joinedload(Question.answers))
            .order_by(func.random())
            .limit(1)
            )
    result = await session.execute(stmt)
    return result.scalar()
