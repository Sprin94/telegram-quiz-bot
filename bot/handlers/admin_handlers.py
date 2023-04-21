from random import shuffle

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, PollAnswer
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession

from database.schemas import QuestionSchema, AnswerSchema
from database.crud import create_question_with_answers, get_random_quiz

router: Router = Router(name="admin-router")

REDIS_TEMP = {}


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
    question = QuestionSchema(
        chat_id=message.chat.id,
        text=message.text.lower()
    )
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
    answer = AnswerSchema(
        text=message.text,
        is_right=False if answers else True,
    )
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


@router.message(Command(commands=['poll']))
async def create_poll(message: Message, bot: Bot, session: AsyncSession):
    quiz = await get_random_quiz(session=session, chat_id=message.chat.id)
    shuffle(quiz.answers)
    answers = []
    for i, answer in enumerate(quiz.answers):
        answers.append(answer.text)
        if answer.is_right:
            correct_option_id = i
    poll_message = await bot.send_poll(
        chat_id=message.chat.id,
        question=quiz.text,
        type='quiz',
        correct_option_id=correct_option_id,
        options=answers,
        is_anonymous=False,
    )
    REDIS_TEMP[poll_message.poll.id] = {
        'chat_id': message.chat.id,
        'correct_answer': correct_option_id,
    }


@router.poll_answer()
async def poll_answer(poll_answer: PollAnswer, bot: Bot):
    poll_correct_answer = REDIS_TEMP.get(poll_answer.poll_id)
    if poll_correct_answer:
        if poll_correct_answer['correct_answer'] == poll_answer.option_ids[0]:
            chat_id = REDIS_TEMP.get(poll_answer.poll_id)['chat_id']
            REDIS_TEMP.pop(poll_answer.poll_id)
            await bot.send_message(
                chat_id=chat_id,
                text=(f'{poll_answer.user.username} первый ответил '
                      'правильно и получает немного кармы =)')
            )
