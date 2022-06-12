import contextlib
from typing import Optional, AsyncIterator

import asyncpg

import config


class DatabaseCreate:

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def create_tables(self):
        sql = """
        CREATE TABLE IF NOT EXISTS type_student_list (
        id SERIAL PRIMARY KEY,
        name text
        );
        
        CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        full_name character varying(255) NOT NULL,
        username character varying(255),
        telegram_id bigint NOT NULL UNIQUE,
        datebirth date,
        custom_name character varying(255),
        time_created timestamp without time zone DEFAULT timezone('utc'::text, now()),
        type_student_id integer REFERENCES type_student_list(id)
        );
        
        CREATE TABLE IF NOT EXISTS action_code_list (
        id integer PRIMARY KEY,
        name text,
        type text
        );
        
        CREATE TABLE IF NOT EXISTS data_log (
        id SERIAL PRIMARY KEY,
        code_id integer REFERENCES action_code_list(id),
        change_data text,
        new_data text,
        time_created timestamp without time zone DEFAULT timezone('utc'::text, now()),
        user_id integer REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS courses_list (
        id SERIAL PRIMARY KEY,
        name character varying(255),
        description text,
        duration integer,
        tag json
        );
        
        CREATE TABLE IF NOT EXISTS theme_courses (
        id SERIAL PRIMARY KEY,
        course_id integer REFERENCES courses_list(id),
        name text,
        duration integer
        );
        
        CREATE TABLE IF NOT EXISTS level_exp_list (
        id SERIAL PRIMARY KEY,
        name text
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
        await self.close()
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
