from dataclasses import dataclass

from aiogram import Bot, types
from aiogram.filters import BaseFilter

from cache import admin_cache
from services.utils import get_admins_id_set


@dataclass
class IsAdmin(BaseFilter):
    def get_user_id(self, message: types.Message, bot: Bot) -> int:
        return message.from_user.id

    async def _get_chat_member(self, message: types.Message, bot: Bot) -> bool:
        admins = admin_cache.get(message.chat.id)
        if not admins:
            admins = await get_admins_id_set(chat_id=message.chat.id, bot=bot)
        target_user_id = self.get_user_id(message, bot)
        if target_user_id not in admins:
            return False
        return True

    async def __call__(self, message: types.Message, bot: Bot):
        chat_member = await self._get_chat_member(message, bot)
        if not chat_member:
            return False
        return True
