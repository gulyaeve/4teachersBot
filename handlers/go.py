"""
Хэндлер команды /go, для сбора информации о курсе
"""
from datetime import datetime
from logging import log, INFO

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from filters import AuthCheck
from loader import dp, db
from utils.utilities import make_keyboard_list, validate


class Course(StatesGroup):
    Name = State()
    Direction = State()
    LevelExp = State()
    LevelUser =State()
    UserPlan = State()
    UserDayPlan = State()
    UserDateStart = State()


@dp.message_handler(AuthCheck(), commands=['go'])
async def start_course(message: types.Message):
    await message.reply("Чтобы помочь тебе сохранять фокус ответь на несколько моих вопросов. 😇")
    await message.answer("С чем связан твой курс? (Например: <code>Python</code> или <code>Data Scientist</code>)")
    await Course.Name.set()


@dp.message_handler(commands=['go'])
async def start_course(message: types.Message):
    await message.reply("Мне нужно получше познакомиться с тобой, набери <b>/start</b> и ответь на мои вопросы 😃")


@dp.message_handler(state=Course.Name)
async def purpose_name(message: types.Message, state: FSMContext):
    courses = await db.find_course(f'%{message.text}%')
    if courses:
        inline_keyboard = InlineKeyboardMarkup()
        for course in courses:
            inline_button = InlineKeyboardButton(course["name"], callback_data=f"course_{course['id']}")
            inline_keyboard.add(inline_button)
        await message.answer("Уточни, на каком курсе ты обучаешся:", reply_markup=inline_keyboard)
        await Course.Direction.set()
    else:
        await message.answer("Таких курсов нет, попробуй снова <b>/go</b>")
        await state.finish()


@dp.callback_query_handler(Regexp('course_([0-9]*)'), state=Course.Direction)
async def course_callback(callback: types.CallbackQuery, state: FSMContext):
    course = await db.select_courses(id=int(callback.data.split("_")[1]))
    async with state.proxy() as data:
        data["course_id"] = int(course["id"])
    buttons = []
    level_exps = await db.select_levels()
    for level_exp in level_exps:
        buttons.append(level_exp["name"])
    keyboard = make_keyboard_list(buttons)
    await callback.message.answer(f"Отличный выбор. А ты знаешь, что более 50% слушателей выбирают {course['name']} "
                                  f"и кардинально меняют свою профессиональную деятельность.\n"
                                  f"Как с тобой связана данная тема?", reply_markup=keyboard)
    await Course.LevelExp.set()


@dp.message_handler(state=Course.LevelExp)
async def level_exp_set(message: types.Message, state: FSMContext):
    try:
        level_exp = await db.select_level(name=message.text)
        async with state.proxy() as data:
            data["level_exp_id"] = int(level_exp["id"])
        await message.reply("Оцени на сколько ты владеешь данной темой? (от 1 до 5, где 5 - владение в совершенстве)",
                            reply_markup=ReplyKeyboardRemove())
        await Course.LevelUser.set()
    except:
        return await message.answer("Выбери пожалуйста на клавиатуре:")


@dp.message_handler(Regexp("^[1-5]"), state=Course.LevelUser)
async def level_user_set(message: types.Message, state: FSMContext):
    data = await state.get_data()
    themes = await db.select_theme_courses(course_id=data['course_id'])
    # log(INFO, themes)
    msg = "Пока мы с тобой болтали я загрузил программу и готов ее адаптировать под тебя. Вот она:\n"
    for theme in themes:
        msg += f" 🔸 <i>{theme['name']}</i> - {theme['duration']} часа-ов\n"
    course_duration = await db.calculate_hours(course_id=data['course_id'])
    log(INFO, course_duration['sum'])
    # course_duration = 592
    msg += f" 🔹 Всего <b>{course_duration['sum']}</b> часов."
    async with state.proxy() as data:
        data["level_user"] = int(message.text)
        data["course_duration"] = course_duration['sum']
    await message.answer(msg)
    await message.answer("Рутинные дела никто не отменял поэтому, сколько часов ты планируешь заниматься в неделю?")
    await Course.UserPlan.set()


@dp.message_handler(state=Course.LevelUser)
async def level_user_set(message: types.Message, state: FSMContext):
    return await message.answer(f"Ты ввел {message.text} и это не подходит. Введи число от 1 до 5.")


@dp.message_handler(Regexp("([0-9]*)"), state=Course.UserPlan)
async def user_plan_set(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_hours_per_week'] = message.text
    await message.answer("А в день?")
    await Course.UserDayPlan.set()


@dp.message_handler(state=Course.UserPlan)
async def user_plan_set(message: types.Message, state: FSMContext):
    return await message.answer("Введи число пожалуйста.")


@dp.message_handler(Regexp("([0-9]*)"), state=Course.UserDayPlan)
async def user_day_plan_set(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_hours_per_day'] = message.text
    data = await state.get_data()
    calculated_hours_per_day = data['user_hours_per_week'] // 6
    if calculated_hours_per_day != data['user_hours_per_day']:
        return await message.reply("Что-то пошло не так. При таком раскладе в день надо заниматься около 5 часов "
                                   "или в неделю 12 часов. Воскресенье - это святое, отдых.")
    else:
        await message.answer("Рассчитал индивидуальный план. Давай сверим, что у меня получилось с твоими ожиданиями. "
                             "Когда ты планируешь приступить к занятиям?")
        await Course.UserDateStart.set()


@dp.message_handler(state=Course.UserDayPlan)
async def user_plan_set(message: types.Message, state: FSMContext):
    return await message.answer("Введи число пожалуйста.")


@dp.message_handler(state=Course.UserDateStart)
async def user_date_start_set(message: types.Message, state: FSMContext):
    if await validate(message.text):
        data = await state.get_data()
        date = datetime.strptime(message.text, '%Y-%m-%d')
        if date < datetime.now():
            return await message.reply("Введи корректную дату.")
        months = round(data['course_duration'] / data['user_hours_per_week'] / 3, 0)
        data_finish = date + months
    else:
        return await message.reply("Введи корректную дату.")
