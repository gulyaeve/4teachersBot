import contextlib
from typing import Optional, AsyncIterator

import asyncpg

import config


class DatabaseUsers:

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        full_name character varying(255) NOT NULL,
        username character varying(255),
        telegram_id bigint NOT NULL UNIQUE,
        datebirth date,
        custom_name character varying(255),
        time_created timestamp without time zone DEFAULT timezone('utc'::text, now())
        );
        """
        await self.execute(sql, execute=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f"{item} = ${num}" for num, item in enumerate(parameters.keys(),
                                                          start=1)
        ])
        return sql, tuple(parameters.values())

    async def add_user(self, full_name, username, telegram_id):
        sql = "INSERT INTO users (full_name, username, telegram_id) VALUES($1, $2, $3) returning *"
        return await self.execute(sql, full_name, username, telegram_id, fetchrow=True)

    async def update_user_fullname(self, full_name, telegram_id):
        sql = "UPDATE users SET full_name=$1 WHERE telegram_id=$2"
        return await self.execute(sql, full_name, telegram_id, execute=True)

    async def update_user_username(self, username, telegram_id):
        sql = "UPDATE users SET username=$1 WHERE telegram_id=$2"
        return await self.execute(sql, username, telegram_id, execute=True)

    async def update_user_customname(self, custom_name, telegram_id):
        sql = "UPDATE users SET custom_name=$1 WHERE telegram_id=$2"
        return await self.execute(sql, custom_name, telegram_id, execute=True)

    async def update_user_datebirth(self, datebirth, telegram_id):
        sql = "UPDATE users SET datebirth=$1 WHERE telegram_id=$2"
        return await self.execute(sql, datebirth, telegram_id, execute=True)

    async def select_all_users(self):
        sql = "SELECT * FROM users"
        return await self.execute(sql, fetch=True)

    async def select_user(self, **kwargs):
        sql = "SELECT * FROM users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def count_users(self):
        sql = "SELECT COUNT(*) FROM users"
        return await self.execute(sql, fetchval=True)

    async def delete_user(self, telegram_id):
        await self.execute("DELETE FROM users WHERE telegram_id=$1", telegram_id, execute=True)

    async def delete_users(self):
        await self.execute("DELETE FROM users WHERE TRUE", execute=True)

    async def drop_users(self):
        await self.execute("DROP TABLE IF EXISTS users", execute=True)

    async def execute(self, command, *args,
                      fetch: bool = False,
                      fetchval: bool = False,
                      fetchrow: bool = False,
                      execute: bool = False
                      ):
        async with self._transaction() as connection:  # type: asyncpg.Connection
            if fetch:
                result = await connection.fetch(command, *args)
            elif fetchval:
                result = await connection.fetchval(command, *args)
            elif fetchrow:
                result = await connection.fetchrow(command, *args)
            elif execute:
                result = await connection.execute(command, *args)
        return result

    # Это можно просто скопировать для корректной работы с соединениями
    @contextlib.asynccontextmanager
    async def _transaction(self) -> AsyncIterator[asyncpg.Connection]:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                user=config.DB_USER,
                password=config.DB_PASS,
                host=config.DB_HOST,
                database=config.DB_NAME,
                port=config.DB_PORT
            )
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            async with conn.transaction():
                yield conn

    async def close(self) -> None:
        if self._pool is None:
            return None

        await self._pool.close()
