"""
Хэндлер команды /go, для сбора информации о курсе
"""
from aiogram import types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


from filters import AuthCheck
from loader import dp, db_courses
from utils.utilities import make_keyboard_list


class Course(StatesGroup):
    Name = State()
    Duration = State()
    Week = State()
    Connect = State()
    Hold = State()


@dp.message_handler(AuthCheck(), commands=['go'])
async def start_course(message: types.Message):
    await message.reply("Чтобы помочь тебе сохранять фокус ответь на несколько моих вопросов. 😇")
    await message.answer("С чем связан твой курс? (Например: <code>Python</code>)")
    await Course.Name.set()


@dp.message_handler(commands=['go'])
async def start_course(message: types.Message):
    await message.reply("Мне нужно получше познакомиться с тобой, набери <b>/start</b> и ответь на мои вопросы 😃")


@dp.message_handler(state=Course.Name)
async def purpose_name(message: types.Message):
    courses = await db_courses.find_course(f'%{message.text}%')
    inline_keyboard = InlineKeyboardMarkup()
    for course in courses:
        inline_button = InlineKeyboardButton(course["name"], callback_data=course["id"])
        inline_keyboard.add(inline_button)
    await message.answer("Уточни, на каком курсе ты обучаешся:", reply_markup=inline_keyboard)
    # print(courses)
    # await message.answer(courses)
    # await message.answer("Сколько длится весь курс?")
    # await Course.Duration.set()


# @dp.message_handler(state=Course.Duration)
# async def purpose_duration(message: types.Message):
#     await message.answer("Сколько времени в неделю ты готов(а) уделять в неделю?")
#     await Course.Week.set()
#
#
# @dp.message_handler(state=Course.Week)
# async def purpose_week(message: types.Message):
#     buttons = ["это моя работа", "это мое хобби", "хочу начать жизнь заново", "просто для интереса", "для учебы"]
#     keyboard = make_keyboard_list(buttons)
#     await message.answer("Как с тобой связана данная тема?", reply_markup=keyboard)
#     await Course.Connect.set()
#
#
# @dp.message_handler(state=Course.Connect)
# async def purpose_connect(message: types.Message):
#     await message.answer("Оцени (от 1 до 5) свой уровень владения данной темой?")
#     await Course.Hold.set()
#
#
# @dp.message_handler(state=Course.Hold)
# async def purpose_hold(message: types.Message):
#     await message.answer("Начиная изучать что-то, мы становимся на путь изменений и перемен. Если бы ты писал книгу о "
#                          "переменах, то для того, чтобы лучше всего передать будущим читателям максимум знаний, тебе "
#                          "бы понадобилось:")
#     await Course.Hold.set()
