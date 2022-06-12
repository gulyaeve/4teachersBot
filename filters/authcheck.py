from logging import log, INFO

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from loader import db


class AuthCheck(BoundFilter):
    async def check(self, message: types.Message):
        """
        Фильтр для проверки заполнения анкеты пользователем
        """
        try:
            user = await db.select_user(telegram_id=message.from_user.id)
            if user["datebirth"] is None:
                log(INFO, f"Пользователь не прошёл регистрацию [{message.from_user.id}]")
                return False
            else:
                log(INFO, f"[{message.from_user.id}] пользователь прошёл регистрацию: [{user['datebirth']}]")
                return True
        except Exception as err:
            log(INFO, f"[{message.from_user.id}] Пользователь не найден. {err}")
            return False
