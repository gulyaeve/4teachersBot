from logging import log, INFO

from aiogram import types

from config import bot_admin
from loader import bot
import re


async def set_default_commands():
    return await bot.set_my_commands([
        types.BotCommand(command="/start", description="Начать работу с чат-ботом"),
        types.BotCommand(command="/help", description="Помощь по командам чат-бота"),
    ])


async def notify_admins(message):
    try:
        await bot.send_message(bot_admin, message)
    except:
        log(INFO, f"Admin [{bot_admin}] block this bot")


def get_key(d: dict, value):
    for k, v in d.items():
        if v == value:
            return k


def make_keyboard(buttons: dict):
    keyboard = types.ReplyKeyboardMarkup()
    for button in buttons.values():
        keyboard.add(button)
    keyboard.add("ОТМЕНА")
    return keyboard


def make_text(input_text):
    return re.sub(r'<.*?>', '', input_text)
