"""
Хэндлер команды /go, для сбора информации о курсе
"""
from datetime import timedelta, datetime
from logging import log, INFO

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, InputFile

from filters import AuthCheck
from loader import dp, db
from utils.utilities import make_keyboard_list, validate


class Course(StatesGroup):
    Name = State()
    Direction = State()
    LevelExp = State()
    LevelUser = State()
    UserPlan = State()
    UserDayPlan = State()
    UserDateStart = State()


@dp.message_handler(AuthCheck(), commands=['go'])
async def start_course(message: types.Message):
    stiker_smile = await db.select_stiker(emoji="thinking")
    await message.answer_sticker(stiker_smile['code'])
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
    msg += f" 🔹 Всего <b>{course_duration['sum']}</b> часов."
    async with state.proxy() as data:
        data["level_user"] = int(message.text)
        data["course_duration"] = course_duration['sum']
    confused_sticker = await db.select_stiker(emoji='confused')
    await message.answer_sticker(confused_sticker['code'])
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
    calculated_hours_per_day = int(data['user_hours_per_week']) // 6
    if calculated_hours_per_day != int(data['user_hours_per_day']):
        await message.reply(f"Что-то пошло не так. При таком раскладе в день надо заниматься около "
                            f"{int(data['user_hours_per_week'])} часов "
                            f"или в неделю {int(data['user_hours_per_day']) * 6} часов. "
                            f"Воскресенье - это святое, отдых.")
        await message.answer("Введи ещё раз сколько часов ты хочешь заниматься в неделю?")
        await Course.UserPlan.set()
    else:
        await message.answer("Рассчитал индивидуальный план. Давай сверим, что у меня получилось с твоими ожиданиями. "
                             "Когда ты планируешь приступить к занятиям?")
        await Course.UserDateStart.set()


@dp.message_handler(state=Course.UserDayPlan)
async def user_plan_set(message: types.Message, state: FSMContext):
    return await message.answer("Введи число пожалуйста.")


@dp.message_handler(state=Course.UserDateStart)
async def user_date_start_set(message: types.Message, state: FSMContext):
    user = await db.select_user(telegram_id=message.from_user.id)
    input_date = f"{message.text.split('.')[2]}-{message.text.split('.')[1]}-{message.text.split('.')[0]}"
    if await validate(input_date):
        data = await state.get_data()
        course_duration = int(data['course_duration'])
        user_hours_per_day = int(data['user_hours_per_day'])
        date_start = datetime.strptime(input_date, '%Y-%m-%d')
        today = datetime.today()
        weeks = round(course_duration / user_hours_per_day / 6, 0) + \
                round(round(course_duration / user_hours_per_day / 6, 0) / 3, 0)
        day_finish = date_start + timedelta(weeks=weeks)
        day_finish_rus = datetime.strftime(day_finish, '%d.%m.%Y')
        if date_start < today:
            return await message.reply("Я согласен с тем, что надо было начинать раньше, но второе лучшее время "
                                       "это сейчас) или завтра) 😅")
        else:
            new_course = await db.add_course(user['id'], date_start, day_finish,
                                             data['level_exp_id'], data['level_user'], data['course_id'])
            await db.add_log(2, user['id'], str(data['course_id']), None)
            log(INFO, f"[{message.from_user.id}] start course [{new_course}]")
            laughing_sticker = await db.select_stiker(emoji='laughing')
            await message.answer_sticker(laughing_sticker['code'])
            await message.answer(f"Расчетное время окончания обучения <b>{day_finish_rus}</b>, "
                                 f"как только у тебя появится больше времени для обучения пиши мне <b>/finish</b> "
                                 f"и я cкорректирую индивидуальную траектория обучения.")
            count_user_courses = await db.count_user_courses(user['id'])
            achievement_start = await db.count_user_achievement(user['id'], 1)
            await state.finish()
            if count_user_courses['count'] == 1 and achievement_start['count'] == 0:
                await db.add_achievement(1, user['id'])
                achievement = await db.select_achievement(id=1)
                log(INFO, f"[{message.from_user.id}] get achievement {achievement['name']}")
                await message.answer(f"🏆 Поздравляю! Достижение открыто!\n"
                                     f"<b>{achievement['name']}</b>")
                await message.answer_photo(InputFile(f"{achievement['image']}"))
    else:
        return await message.reply("Введи корректную дату.")
