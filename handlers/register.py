"""
Хэндлер для регистрации пользователя
"""
from logging import log, INFO

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove

from utils import utilities
from loader import dp, bot, db_users, db_log
import datetime

from utils.utilities import make_keyboard_list


async def validate(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return 1
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


class Register(StatesGroup):
    Name = State()
    NameSet = State()
    Age = State()
    Type = State()


@dp.message_handler(commands=['start'])
async def start_register(message: types.Message):
    user = await db_users.select_user(telegram_id=message.from_user.id)
    if user["custom_name"] is None:
        fullname = user["full_name"]
    else:
        fullname = user["custom_name"]
    log(INFO, f"USER [{message.from_user.id}] нажал START.")
    me = await bot.get_me()
    buttons = [f"{message.from_user.full_name}", "Задать другое имя"]
    keyboard = utilities.make_keyboard_list(buttons)
    await message.reply(f"Привет, {fullname}. 🙋🏻‍♂️\n"
                        f"Я {me.full_name} - бот-помощник 🤖, буду помогать тебе рефлексировать пройденный материал, "
                        f"держать в фокусе цель обучения и ее достижение.")
    await message.answer("Как я могу к тебе обращаться?", reply_markup=keyboard)
    await Register.Name.set()


@dp.message_handler(Text(equals="Задать другое имя"), state=Register.Name)
async def new_name(message: types.Message):
    await message.reply("Введи имя для обращения:",
                        reply_markup=ReplyKeyboardRemove())
    await Register.NameSet.set()


@dp.message_handler(state=Register.NameSet)
async def new_name(message: types.Message):
    newname = message.text
    user = await db_users.select_user(telegram_id=message.from_user.id)
    await db_log.add_log(1, user["id"], newname, user["custom_name"])
    await db_users.update_user_customname(newname, message.from_user.id)
    await message.reply(f"Теперь я буду называть тебя {newname}!")
    log(INFO, f"[{message.from_user.id}] saved custom_name {newname}")
    await message.answer("Введите дату рождения")
    await Register.Age.set()


@dp.message_handler(state=Register.Name)
async def new_name(message: types.Message):
    user = await db_users.select_user(telegram_id=message.from_user.id)
    fullname = message.from_user.full_name
    await message.reply(f"Хорошо, {fullname}", reply_markup=ReplyKeyboardRemove())
    log(INFO, f"[{message.from_user.id}] saved fullname {fullname}")
    await db_users.update_user_customname(None, message.from_user.id)
    await db_log.add_log(1, user["id"], None, user["custom_name"])
    await message.answer("Введите дату рождения")
    await Register.Age.set()


@dp.message_handler(state=Register.Age)
async def set_age(message: types.Message, state: FSMContext):
    date = f"{message.text.split('.')[2]}-{message.text.split('.')[1]}-{message.text.split('.')[0]}"
    if await validate(date):
        await db_users.update_user_datebirth(datetime.datetime.strptime(date, '%Y-%m-%d'), message.from_user.id)
        log(INFO, f"[{message.from_user.id}] saved age {date}")
        buttons = []
        user_types = await db_users.select_all_types()
        for user_type in user_types:
            buttons.append(user_type["Description"])
        keyboard = make_keyboard_list(buttons)
        await message.reply(f"Начиная изучать что-то, мы становимся на путь изменений и перемен. Если бы ты писал "
                            f"книгу о переменах, то для того, чтобы лучше всего передать будущим читателям максимум "
                            f"знаний, тебе бы понадобилось:", reply_markup=keyboard)
        await Register.Type.set()
    else:
        return await message.reply(f"Введи пожалуйста в формате ДД.ММ.ГГГГ")


@dp.message_handler(state=Register.Type)
async def set_type(message: types.Message, state: FSMContext):
    try:
        user_type = await db_users.select_type(description=message.text)
        await db_users.update_user_type_student(user_type['id'], message.from_user.id)
        await message.reply(f"Отлично! Теперь тебе доступна команда <b>/go</b> для отслеживания своего прогресса.",
                            reply_markup=ReplyKeyboardRemove())
        log(INFO, f"[{message.from_user.id}] saved type {user_type['name']}")
        await state.finish()
    except:
        return await message.answer("Выбери пожалуйста на клавиатуре:")
