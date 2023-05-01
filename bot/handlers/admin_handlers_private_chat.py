from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from database.schemas import QuestionSchema, AnswerSchema
from database.crud import (
    create_question_with_answers, get_questions_by_chat_id, get_question_with_answers,
)
from keyboards.admin_quiz import get_remove_quiz_keyboard
from services.utils import get_admins_id_set

router: Router = Router(name="admin-group")


class SettingsQuiz(StatesGroup):
    manage = State()
    create_question = State()
    create_answers = State()


@router.message(Command(commands=['manage']))
async def check(message: Message, bot: Bot, state: FSMContext, command: CommandObject):
    if not command.args:
        return await message.answer('Неправильное использование команды.\n'
                                    'Используй /manage <chat_id>')
    if command.args[0] != '-':
        return await message.answer('ID групп начинается с "-"')
    try:
        chat_id = int(command.args)
    except ValueError:
        return await message.answer('ID чата должно быть целым числом и начинаться с "-"')
    try:
        admins = await get_admins_id_set(chat_id, bot)
    except TelegramBadRequest:
        return await message.answer('Не найден чат с таким ID')
    if message.from_user.id not in admins:
        return await message.answer(f'Вы не админ в чате с ID: {chat_id}')
    await message.answer('Для создания опроса  /create\n'
                         'Для просмотра списка опросов и получения ID вопросов /quizzes\n'
                         'Для просмотра вопроса с ответами или удаления  /detail <id>\n')
    await state.set_state(SettingsQuiz.manage)
    await state.set_data({'chat_id': chat_id})


@router.message(SettingsQuiz.manage, Command(commands=['quizzes']))
async def get_chat_questions(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    questions = await get_questions_by_chat_id(
        session=session,
        chat_id=data['chat_id']
    )
    if not questions:
        await message.answer('Не нашел опросов для этого чата.\n'
                             'Чтобы создать опрос используйте /manage_quiz')
    res = '\n'.join(f'{i}. {q.text} id:{q.id}'
                    for i, q in enumerate(questions, start=1))
    return await message.answer(
        f'Вот список опросов для этого чата:\n{res}'
    )


@router.message(SettingsQuiz.manage, Command(commands=['detail']))
async def get_question(
    message: Message,
    session: AsyncSession,
    command: CommandObject,
    state: FSMContext,
):
    if not command.args:
        await message.answer('Пожалуйста, укажите номер вопроса после команды /detail')
        return
    try:
        question_id = int(command.args)
    except ValueError:
        return await message.answer('Номер должен быть целым числом')
    question = await get_question_with_answers(session=session, question_id=question_id)
    if question:
        data = await state.get_data()
        if question.chat_id != data['chat_id']:
            return await message.answer('Этот вопрос не из этого чата.')
        res = '\n'.join(f'{i}. {answer.text} {answer.is_right}'
                        for i, answer in enumerate(question.answers, start=1))
        return await message.answer(
            f'Вопрос:\n{question.text}\nОтветы:\n{res}\n#<b>{question_id}</b>',
            reply_markup=get_remove_quiz_keyboard(),
            parse_mode='HTML',
        )
    await message.answer('Не удалось найти вопрос с таким id.')


@router.message(SettingsQuiz.manage, Command(commands=['create']))
async def create_quiz(message: Message, state: FSMContext):
    await message.answer(
        text=(
            'Допустимая длинна вопроса от 1 до 300 символов.\n'
            'Введите вопрос для добавления:'
        ),
    )
    await state.set_state(SettingsQuiz.create_question)


@router.message(SettingsQuiz.create_question, F.text, ~(F.text.startswith('/')))
async def add_question(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        question = QuestionSchema(
            chat_id=data['chat_id'],
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
    await state.set_state(SettingsQuiz.create_answers)


@router.message(SettingsQuiz.create_answers, F.text, ~(F.text.startswith('/')))
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
        return await message.answer('Ваш ответ слишком длинный.')

    answers = user_data.setdefault('answers', [])
    answers.append(answer)
    await state.update_data(**user_data)
    answer_amount = len(answers)
    await message.answer(
        text=(f'Добавлено {answer_amount} ответ(ов) из 4.')
    )
    if answer_amount == 4:
        await state.set_state(SettingsQuiz.manage)
        await state.set_data({'chat_id': user_data['chat_id']})
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
