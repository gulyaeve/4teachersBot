from aiogram import Dispatcher
from .authcheck import AuthCheck


def setup(dp: Dispatcher):
    dp.filters_factory.bind(AuthCheck)
