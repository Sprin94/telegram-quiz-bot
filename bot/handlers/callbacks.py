from aiogram import Router
from aiogram.types import CallbackQuery

from handlers.callback_data import DetailQuiz

router = Router()


@router.callback_query(DetailQuiz.filter())
async def callback_quiz_detail(callback: CallbackQuery, callback_data: DetailQuiz):
    if callback_data.flag == 'remove':
        await callback.answer('Позже сделаю', show_alert=True)
    await callback.answer()
