from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot_responses import commands_response as text

router = Router()


@router.message(Command(commands=['start', 'help']))
async def cmd_start(message: Message):
    await message.answer(
        text=text.START_AND_HELP_TEXT,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command(commands=['command']))
async def cmd_command(message: Message):
    await message.answer(
        text=text.COMMAND,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command(commands=['cancel']))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text='Состояние сброшено.',
        reply_markup=ReplyKeyboardRemove()
    )
