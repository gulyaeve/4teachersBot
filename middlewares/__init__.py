from .db import DB_middleware

from loader import dp

if __name__ == "middlewares":
    dp.middleware.setup(DB_middleware())