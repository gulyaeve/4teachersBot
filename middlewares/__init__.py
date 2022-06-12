from .db import DBmiddleware

from loader import dp

if __name__ == "middlewares":
    dp.middleware.setup(DBmiddleware())