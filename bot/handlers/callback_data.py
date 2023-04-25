from aiogram.filters.callback_data import CallbackData


class DetailQuiz(CallbackData, prefix='detail_quiz'):
    flag: str
