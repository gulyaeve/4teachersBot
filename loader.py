import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import telegram_token
from utils.db_api.db_courses import DatabaseCourses
from utils.db_api.db_users import DatabaseUsers
from utils.db_api.db_logging import DatabaseLogging

# ChatBot objects
bot = Bot(token=telegram_token, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Database objects
db_users = DatabaseUsers()
db_log = DatabaseLogging()
db_courses = DatabaseCourses()

# Logging setup
logging.basicConfig(handlers=(logging.FileHandler('logs/log.txt'), logging.StreamHandler()),
                    format=u'%(asctime)s %(filename)s [LINE:%(lineno)d] #%(levelname)-15s %(message)s',
                    level=logging.INFO,
                    )
