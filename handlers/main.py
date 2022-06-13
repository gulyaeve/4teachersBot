from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from logging import log, INFO

from loader import dp


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_message = """
    Помощь по командам:\n
    <b>/start</b> - начало взаимодействия с ботом;\n
    <b>/go</b> - Начать отслеживать свой прогресс;\n
    <b>/cancel</b> - отмена текущего действия;\n
    """
    await message.answer(help_message)


# @dp.message_handler(commands=['start'])
# async def cmd_start_user(message: types.Message):
#     """
#     Conversation's entry point
#     """
#     log(INFO, f"USER [{message.from_user.id}] нажал START.")
#     me = await bot.get_me()
#     await message.reply(f"Добро пожаловать в чат-бот {me.full_name}!")
#     await message.answer("Чтобы начать отслеживать свой прогресс выбери команду: <b>/go</b>")


# You can use state '*' if you need to handle all states
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
@dp.message_handler(state='*', commands=['cancel'])
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    log(INFO, f"[{message.from_user.id}] отменил действие.")
    await state.finish()
    await message.reply('Действие отменено.', reply_markup=types.ReplyKeyboardRemove())
