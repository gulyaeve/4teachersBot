from loader import bot, storage, dp, db_users, db_log, db_courses
from utils.utilities import set_default_commands, notify_admins
import filters, middlewares, handlers
from aiogram import executor


async def on_shutdown(dp):
    await bot.delete_my_commands()
    # await notify_admins("Бот выключен...")
    await storage.close()
    await bot.close()


async def on_startup(dp):
    await set_default_commands()
    await db_users.create_table_users()
    await db_log.create_table_datalog()
    await db_courses.create_table_courses()
    await notify_admins("Бот запущен и готов к работе.")


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=on_shutdown, on_startup=on_startup)
