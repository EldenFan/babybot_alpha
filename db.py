import random
import aiosqlite
from config import admin_id
from datetime import datetime


async def init() -> None:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        await db.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        points INTEGER DEFAULT 0,
                        message_time DATETIME
                    )
                ''')

        await db.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        category_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        drop_rate REAL NOT NULL DEFAULT 100,
                        give_points INTEGER,
                        delay INTEGER
                    )
                ''')

        # В конце - это вероятность дропа, название можешь сам поменять
        await db.execute('''INSERT OR IGNORE INTO categories (category_id, name, drop_rate, give_points, delay) 
                    VALUES (1, "Отлично", 5, 100, 0)''')
        await db.execute('''INSERT OR IGNORE INTO categories (category_id, name, drop_rate, give_points, delay) 
                    VALUES (2, "Хорошо", 45, 5, 30)''')
        await db.execute('''INSERT OR IGNORE INTO categories (category_id, name, drop_rate, give_points, delay) 
                    VALUES (3, "Нормально", 45, 1, 60)''')
        await db.execute('''INSERT OR IGNORE INTO categories (category_id, name, drop_rate, give_points, delay) 
                    VALUES (4, "Плохо", 5, -100, 120)''')

        await db.execute('''
                    CREATE TABLE IF NOT EXISTS packages (
                        package_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL
                    )
                ''')

        await db.execute('''
                    CREATE TABLE IF NOT EXISTS photos (
                        photo_id INTEGER PRIMARY KEY,
                        path TEXT NOT NULL,
                        score INTEGER DEFAULT 0,
                        votes INTEGER DEFAULT 0
                    )
        ''')

        await db.execute('''
                    CREATE TABLE IF NOT EXISTS package_photos (
                        connection_id INTEGER PRIMARY KEY,
                        photo_id INTEGER,
                        package_id INTEGER,
                        FOREIGN KEY (package_id) REFERENCES packages (package_id)
                        FOREIGN KEY (photo_id) REFERENCES photos (photo_id)
                    )
                ''')

        await db.execute('''
                    CREATE TABLE IF NOT EXISTS package_category (
                        package_category_id INTEGER PRIMARY KEY,
                        package_id INTEGER,
                        category_id INTEGER,
                        user_id INTEGER,
                        FOREIGN KEY (package_id) REFERENCES packages (package_id),
                        FOREIGN KEY (category_id) REFERENCES categories (category_id)
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')

        await db.commit()


# Функция для добавления пользователя
async def add_user(user_id) -> None:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        await db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        await db.commit()


# Функция для получения всей инфы о категориях
async def get_categories() -> list:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT * FROM categories') as cursor:
            return await cursor.fetchall()


# Функция для получения пака по категории и пользователю
async def get_packages(category_id, user_id) -> list:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT package_id FROM package_category WHERE category_id = ? AND user_id = ?',
                              (category_id, user_id)) as cursor:
            res = await cursor.fetchall()
        if res:
            return res
        async with db.execute('SELECT package_id FROM package_category WHERE category_id = ? AND user_id = ?',
                              (category_id, admin_id)) as cursor:
            res = await cursor.fetchall()
        return res


# Проверка на наличие пользователя в бд
async def user_exists(user_id) -> bool:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
    return user is not None


# Получение фоток из категории пользователя
async def get_photos_from_category(category_id, user_id) -> list:
    packages = await get_packages(category_id, user_id)
    package_id = random.choice(packages)[0]
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute("SELECT photo_id FROM package_photos WHERE package_id = ?", (package_id,)) as cursor:
            return await cursor.fetchall()


# Получение пути к фото через id
async def get_path(photo_id) -> tuple:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute("SELECT path FROM photo WHERE photo_id = ?", (photo_id,)) as cursor:
            return cursor.fetchone()


# Получение времени отправки следующего сообщения
async def when_user_can_send_message(user_id):
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT message_time FROM users WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()
        if result is None:
            return True
        message_time = result[0]
        return message_time


# Получение задержки
async def get_delay(category_id) -> tuple:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT delay FROM categories WHERE category_id = ?', (category_id,)) as cursor:
            return await cursor.fetchone()


# Изменение времени отправки следующего сообщения
async def update_message_time(user_id, next_time):
    async with aiosqlite.connect('bot_db.sqlite') as db:
        await db.execute('UPDATE users SET message_time = ? WHERE user_id = ?', (next_time, user_id))
        await db.commit()


# Добавление оценки
async def vote_photo(photo_id, new_score) -> None:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT score, votes FROM photos WHERE photo_id = ?', (photo_id,)) as cursor:
            result = await cursor.fetchone()
        if result:
            current_score, current_votes = result
            updated_votes = current_votes + 1
            updated_score = new_score + current_score
            await db.execute('UPDATE photos SET score = ?, votes = ? WHERE photo_id = ?',
                             (updated_score, updated_votes, photo_id))
            await db.commit()


# Средний рейтинг фотки
async def get_average_score(photo_id) -> float:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT score, votes FROM photos WHERE photo_id = ?', (photo_id,)) as cursor:
            result = await cursor.fetchone()
        if result and result[1] > 0:
            score, votes = result
            return score / votes
        else:
            return 0.0
