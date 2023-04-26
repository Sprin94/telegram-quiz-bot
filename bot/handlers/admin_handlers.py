import asyncio
from random import shuffle
from datetime import datetime, time, timedelta

from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, PollAnswer
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from database.schemas import QuestionSchema, AnswerSchema
from database.crud import (
    create_question_with_answers, get_random_quiz, get_questions_by_chat_id,
    get_question_with_answers, create_or_update_schedule, get_schedule
)
from filters.admin_user import IsAdmin
from keyboards.admin_quiz import get_remove_quiz_keyboard
from run import sessionmaker
from cache import schedule_cache, quiz_cache

router: Router = Router(name="admin-router")
router.message.filter(F.chat.type.in_(["group", "supergroup"]), IsAdmin())


class CreateQuiz(StatesGroup):
    create_question = State()
    create_answers = State()


@router.message(Command(commands=['create']))
async def create_quiz(message: Message, state: FSMContext):
    await message.answer(
        text=(
            'Допустимая длинна вопроса от 1 до 300 символов.\n'
            'Введите вопрос для добавления:'
        ),
    )
    await state.set_state(CreateQuiz.create_question)


@router.message(CreateQuiz.create_question, F.text, ~(F.text.startswith('/')))
async def add_question(message: Message, state: FSMContext):
    await state.clear()
    try:
        question = QuestionSchema(
            chat_id=message.chat.id,
            text=message.text.lower()
        )
    except ValidationError:
        await message.answer('Ваш вопрос слишком длинный.')
        return
    await state.update_data(question=question)
    await message.answer(
        text=('Вопрос добавлен\nТеперь добавим варианты ответов.\n'
              'Допустимая длинна каждого ответа от 1 до 100 символов.\n'
              'Первым вводится правильный ответ, следующие'
              ' автоматически помечаются как неправильные.'),
    )
    await state.set_state(CreateQuiz.create_answers)


@router.message(CreateQuiz.create_answers, F.text, ~(F.text.startswith('/')))
async def add_answers(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
):
    user_data = await state.get_data()
    answers = user_data.setdefault('answers', [])
    try:
        answer = AnswerSchema(
            text=message.text,
            is_right=False if answers else True,
        )
    except ValidationError:
        await message.answer('Ваш ответ слишком длинный.')
        return

    answers = user_data.setdefault('answers', [])
    answers.append(answer)
    await state.update_data(**user_data)
    answer_amount = len(answers)
    await message.answer(
        text=(f'Добавлено {answer_amount} ответ(ов) из 4.')
    )
    if answer_amount == 4:
        await state.clear()
        await message.answer('Отлично! Вот что у нас получилось:')
        await bot.send_poll(
            chat_id=message.chat.id,
            question=user_data['question'].text,
            type='quiz',
            correct_option_id=0,
            options=[answer.text for answer in answers],
            is_anonymous=False,
            is_closed=True
        )
        await create_question_with_answers(
            question=user_data['question'],
            answers=user_data['answers'],
            session=session
        )
    elif answer_amount > 4:
        await state.clear()
        await message.answer('Что-то пошло не так. Мы все потеряли.')


@router.message(Command(commands=['quizzes']))
async def get_chat_questions(message: Message, session: AsyncSession, state: FSMContext):
    questions = await get_questions_by_chat_id(session=session, chat_id=message.chat.id)
    if not questions:
        await message.answer('Не нашел опросов для этого чата.\n'
                             'Чтобы создать опрос используйте /create')
    res = '\n'.join(f'{i}. {q.text} id:{q.id}'
                    for i, q in enumerate(questions, start=1))
    await message.answer(
        f'Вот список опросов для этого чата:\n{res}'
    )


@router.message(Command(commands=['detail']))
async def get_question(message: Message, session: AsyncSession, command: CommandObject):
    if not command.args:
        await message.answer('Пожалуйста, укажите номер вопроса после команды /detail')
        return
    try:
        question_id = int(command.args)
    except ValueError:
        await message.answer('Номер должен быть целым числом')
        return
    question = await get_question_with_answers(session=session, question_id=question_id)
    if question:
        if question.chat_id != message.chat.id:
            await message.answer('Этот вопрос не из этого чата.')
            return
        res = '\n'.join(f'{i}. {answer.text} {answer.is_right}'
                        for i, answer in enumerate(question.answers, start=1))
        await message.answer(
            f'Вопрос:\n{question.text}\nОтветы:\n{res}\n#<b>{question_id}</b>',
            reply_markup=get_remove_quiz_keyboard(),
            parse_mode='HTML',
        )
        return
    await message.answer('Не удалось найти вопрос с таким id.')


async def _create_poll(bot: Bot, chat_id: int):
    async with sessionmaker() as session:
        quiz = await get_random_quiz(session=session, chat_id=chat_id)
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


async def _wrapper_for_create_poll(bot: Bot, chat_id: int):
    async with sessionmaker() as session:
        schedule_time = await get_schedule(session=session, chat_id=chat_id)
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


@router.message(Command(commands=['poll']))
async def create_poll_command(message: Message, bot: Bot):
    await _create_poll(bot=bot, chat_id=message.chat.id)


@router.message(Command(commands=['config_time']))
async def set_time_for_poll(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    command: CommandObject,
):
    error_msg = 'Пожалуйста, укажите время проведения опроса.\nПример /config_time 15:15'
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


@router.poll_answer()
async def poll_answer(poll_answer: PollAnswer, bot: Bot):
    poll_correct_answer = quiz_cache.get(poll_answer.poll_id)
    if poll_correct_answer:
        if poll_correct_answer['correct_answer'] == poll_answer.option_ids[0]:
            data = quiz_cache.pop(poll_answer.poll_id)
            await bot.stop_poll(data['chat_id'], data['poll_message_id'])
            await bot.send_message(
                chat_id=data['chat_id'],
                text=(f'@{poll_answer.user.username} первый ответил '
                      'правильно и получает немного кармы =)')
            )
