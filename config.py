from environs import Env

env = Env()
env.read_env()

# Telegram auth:
telegram_token = env.str("TELEGRAM_API_TOKEN")

# Bot admins
bot_admin = env.str("BOT_ADMIN")

# PostgreSQL
DB_USER = env.str("DB_USER")
DB_PASS = env.str("DB_PASS")
DB_HOST = env.str("DB_HOST")
DB_PORT = env.int("DB_PORT")
DB_NAME = env.str("DB_NAME")
