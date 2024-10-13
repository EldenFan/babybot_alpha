import aiosqlite


async def init() -> None:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        await db.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        points INTEGER DEFAULT 0
                    )
                ''')

        await db.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        category_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        drop_rate REAL NOT NULL DEFAULT 100
                    )
                ''')

        # В конце - это вероятность дропа
        await db.execute('INSERT OR IGNORE INTO categories (category_id, name, drop_rate) VALUES (1, "good", 5)')
        await db.execute('INSERT OR IGNORE INTO categories (category_id, name, drop_rate) VALUES (2, "rare good", 45)')
        await db.execute('INSERT OR IGNORE INTO categories (category_id, name, drop_rate) VALUES (3, "rare bad", 45)')
        await db.execute('INSERT OR IGNORE INTO categories (category_id, name, drop_rate) VALUES (4, "bad", 5)')

        await db.execute('''
                    CREATE TABLE IF NOT EXISTS packages (
                        package_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        score INTEGER DEFAULT 0,
                        votes INTEGER DEFAULT 0
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
                        photo_id INTEGER,
                        package_id INTEGER,
                        FOREIGN KEY (package_id) REFERENCES packages (package_id)
                        FOREIGN KEY (photo_id) REFERENCES photos (photo_id)
                    )
                ''')

        await db.execute('''
                    CREATE TABLE IF NOT EXISTS package_category (
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


# Функция для случайного выбора фотографии по категории
async def get_random(category) -> tuple:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT * FROM photos WHERE category = ? ORDER BY RANDOM() LIMIT 1',
                              (category,)) as cursor:
            return await cursor.fetchone()


# Функция для получения текущего голоса пользователя за фото
async def get_user_vote(user_id, photo_id) -> tuple:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT rating FROM votes WHERE user_id = ? AND photo_id = ?',
                              (user_id, photo_id)) as cursor:
            return await cursor.fetchone()


# Функция для добавления или обновления голоса
async def add_vote(user_id, photo_id, new_rating) -> None:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        current_vote = await get_user_vote(user_id, photo_id)

        if current_vote:
            old_rating = current_vote[0]
            await db.execute('UPDATE votes SET score = ? WHERE photo_id = ?',
                             (new_rating, photo_id))

            await db.execute('''
                UPDATE photos 
                SET rating = ((rating * votes) - ? + ?) / votes
                WHERE photo_id = ?
            ''', (old_rating, new_rating, photo_id))
        else:
            await db.execute('INSERT INTO votes (user_id, photo_id, rating) VALUES (?, ?, ?)',
                             (user_id, photo_id, new_rating))

            await db.execute('''
                UPDATE photos 
                SET rating = ((rating * votes) + ?) / (votes + 1), votes = votes + 1 
                WHERE photo_id = ?
            ''', (new_rating, photo_id))

        await db.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (user_id,))
        await db.commit()


# Функция для получения обновленного рейтинга фотографии
async def get_photo_rating(photo_id) -> tuple:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute('SELECT score, votes FROM photos WHERE photo_id = ?', (photo_id,)) as cursor:
            return await cursor.fetchone()


# Проверка на наличие пользователя в бд
async def user_exists(user_id) -> bool:
    async with aiosqlite.connect('bot_db.sqlite') as db:
        async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
    return user is not None
