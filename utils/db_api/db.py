import contextlib
from typing import Optional, AsyncIterator

import asyncpg

import config


class Database:

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
        
        CREATE TABLE IF NOT EXISTS user_courses (
        id integer PRIMARY KEY,
        user_id bigint REFERENCES users(id),
        course_date_start timestamp without time zone DEFAULT timezone('utc'::text, now()),
        course_date_end timestamp without time zone,
        course_date_end_fact timestamp without time zone,
        course_level_exp_id integer REFERENCES level_exp_list(id),
        level_user integer,
        course_id integer REFERENCES courses_list(id)
        );
        
        CREATE TABLE IF NOT EXISTS achievements_list (
        id SERIAL PRIMARY KEY,
        image text,
        name text,
        description text
        );
        
        CREATE TABLE IF NOT EXISTS user_achievements (
        id SERIAL PRIMARY KEY,
        achivements_id text,
        time_reciept timestamp without time zone DEFAULT timezone('utc'::text, now()),
        user_id bigint REFERENCES users(id)
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

    async def update_user_type_student(self, type_student_id, telegram_id):
        sql = "UPDATE users SET type_student_id=$1 WHERE telegram_id=$2"
        return await self.execute(sql, type_student_id, telegram_id, execute=True)

    async def select_all_users(self):
        sql = "SELECT * FROM users"
        return await self.execute(sql, fetch=True)

    async def select_user(self, **kwargs):
        sql = "SELECT * FROM users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_all_types(self):
        sql = "SELECT * FROM type_student_list"
        return await self.execute(sql, fetch=True)

    async def select_type(self, **kwargs):
        sql = "SELECT * FROM type_student_list WHERE "
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

    async def select_theme_courses(self, **kwargs):
        sql = "SELECT * FROM theme_courses WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetch=True)

    async def calculate_hours(self, **kwargs):
        sql = "SELECT SUM(duration) FROM theme_courses WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def add_log(self, code_id, user_id, new_data, change_data):
        sql = "INSERT INTO data_log (code_id, user_id, new_data, change_data) VALUES($1, $2, $3, $4) returning *"
        return await self.execute(sql, code_id, user_id, new_data, change_data, fetchrow=True)

    async def select_all_logs(self):
        sql = "SELECT * FROM data_log"
        return await self.execute(sql, fetch=True)

    async def select_log(self, **kwargs):
        sql = "SELECT * FROM data_log WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_levels(self):
        sql = "SELECT * FROM level_exp_list"
        return await self.execute(sql, fetch=True)

    async def select_level(self, **kwargs):
        sql = "SELECT * FROM level_exp_list WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_courses(self, **kwargs):
        sql = "SELECT * FROM courses_list WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def find_course(self, keyword):
        sql = "SELECT * FROM courses_list WHERE LOWER(name) LIKE LOWER($1)"
        return await self.execute(sql, keyword, fetch=True)

    async def add_course(self, user_id, course_date_start, course_date_end, course_level_exp_id, level_user, course_id):
        sql = "INSERT INTO user_courses (user_id, course_date_start, course_date_end, course_level_exp_id, level_user, course_id) " \
              "VALUES($1, $2, $3, $4, $5, $6) returning *"
        return await self.execute(sql, user_id, course_date_start, course_date_end, course_level_exp_id, level_user, course_id, fetchrow=True)

    async def add_achievement(self, achievement_id, user_id):
        sql = "INSERT INTO user_achivements (achievement_id, user_id) VALUES ($1, $2) returning *"
        return await self.execute(sql, achievement_id, user_id, fetchrow=True)

    async def select_achievement(self, **kwargs):
        sql = "SELECT * FROM achievements_list WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

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
