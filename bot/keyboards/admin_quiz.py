from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.callback_data import DetailQuiz


def get_remove_quiz_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text='Удалить',
            callback_data=DetailQuiz(flag='remove').pack()
        )]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons, )
    return keyboard
