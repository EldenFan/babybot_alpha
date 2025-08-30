import random
import aiosqlite
import os
import asyncio


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
                text TEXT NOT NULL,
                drop_rate REAL NOT NULL DEFAULT 100,
                give_points INTEGER,
                delay INTEGER
            )
        ''')

        await db.execute('''INSERT OR IGNORE INTO categories (category_id, name, text, drop_rate, give_points, delay) 
                    VALUES (1, "Отлично","Поздравляю, у тебя явно есть удача\nСегодня без кд\n\n+100 babyCoin", 5, 100, 0)''')
        await db.execute('''INSERT OR IGNORE INTO categories (category_id, name, text, drop_rate, give_points, delay) 
                    VALUES (2, "Хорошо", "Знаешь, могло быть и хуже\nЛови кд на 30 секунд\n\n+5 babyCoin", 45, 5, 30)''')
        await db.execute('''INSERT OR IGNORE INTO categories (category_id, name, text, drop_rate, give_points, delay) 
                    VALUES (3, "Нормально", "Ты лохазавр, но ещё не лохопендр\nДумаю 60 секунд тебе хватит\n\n+1 babyCoin", 45, 1, 60)''')
        await db.execute('''INSERT OR IGNORE INTO categories (category_id, name, text, drop_rate, give_points, delay) 
                    VALUES (4, "Плохо", 5, "Капец ты лохопендр\nЛови кд на 2 минуты\n\n-100 babyCoin", -100, 120)''')

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
                package_id INTEGER,
                score INTEGER DEFAULT 0,
                votes INTEGER DEFAULT 0,
                FOREIGN KEY (package_id) REFERENCES packages(package_id)
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_category_packages (
                user_id INTEGER,
                category_id INTEGER,
                package_id INTEGER,
                PRIMARY KEY (user_id, category_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id),
                FOREIGN KEY (package_id) REFERENCES packages(package_id)
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

# Получение текста из категорий
async def get_text_from_category(category_id) -> str:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT text FROM categories WHERE category_id = ?', (category_id,)) as cursor:
            result = await cursor.fetchone()
            return str(result)

# Создание нового пакета
async def create_package(name) -> int:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        cursor = await db.execute('INSERT INTO packages (name) VALUES (?)', (name,))
        await db.commit()
        return cursor.lastrowid

# Получение всех пакетов
async def get_all_packages() -> list:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT package_id, name FROM packages') as cursor:
            return await cursor.fetchall()

# Получение названия пакета по ID
async def get_package_name(package_id) -> str:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT name FROM packages WHERE package_id = ?', (package_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else "Неизвестный пакет"

# Добавление фото в пакет
async def add_photo_to_package(path, package_id) -> None:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        await db.execute('INSERT INTO photos (path, package_id) VALUES (?, ?)', (path, package_id))
        await db.commit()

# Получение всех фото в пакете
async def get_photos_in_package(package_id) -> list:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT photo_id, path FROM photos WHERE package_id = ?', (package_id,)) as cursor:
            return await cursor.fetchall()

# Удаление фото из пакета
async def remove_photo_from_package(photo_id) -> None:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT path FROM photos WHERE photo_id = ?', (photo_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                path = result[0]
                if os.path.exists(path):
                    os.remove(path)
        
        await db.execute('DELETE FROM photos WHERE photo_id = ?', (photo_id,))
        await db.commit()

if __name__ == "__main__":
    asyncio.run(init())