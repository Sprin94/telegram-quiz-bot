from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.callback_data import DetailQuiz
from handlers.admin_handlers_private_chat import SettingsQuiz
from database.crud import delete_question
from keyboards.admin_quiz import get_remove_quiz_keyboard


router = Router()


class DeleteQuiz(StatesGroup):
    confirm_delete = State()


@router.callback_query(DeleteQuiz.confirm_delete, DetailQuiz.filter())
async def delete_quiz(
    callback: CallbackQuery,
    callback_data: DetailQuiz,
    session: AsyncSession,
    state: FSMContext,
):
    data = await state.get_data()
    await callback.message.delete()
    await callback.message.reply_to_message.delete()
    await delete_question(session=session, question_id=int(data.get('q_id')))
    await callback.message.answer('Вопрос удалён.')
    await state.set_state(SettingsQuiz.manage)
    await state.set_data({'chat_id': data['chat_id']})


@router.callback_query(DetailQuiz.filter())
async def callback_quiz_detail(
    callback: CallbackQuery,
    callback_data: DetailQuiz,
    state: FSMContext,
):
    if callback_data.flag == 'remove':
        await state.set_state(DeleteQuiz.confirm_delete)
        entities = callback.message.entities
        if entities:
            q_id = entities[0].extract_from(callback.message.text)
            await state.update_data({'q_id': q_id})
        await callback.message.reply(
            f'Вы действительно хотите удалить вопрос с id {q_id}?',
            reply_markup=get_remove_quiz_keyboard()
        )
        await callback.message.delete_reply_markup()
    await callback.answer()
