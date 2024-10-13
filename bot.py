import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import db
from config import TOKEN
from myClass import MyCallback
import os
from datetime import datetime

dp = Dispatcher()


# Выбор категории
async def choose_category() -> int:
    good, rare_good, rare_bad, bad = await db.get_categories()
    categories_arr = [good[0], rare_good[0], rare_bad[0], bad[0]]
    probabilities = [good[2], rare_good[2], rare_bad[2], bad[2]]
    return random.choices(categories_arr, probabilities)[0]


# Создать бд, если её нет
async def on_start() -> None:
    os.makedirs('photos', exist_ok=True)
    await db.init()


# Функция проверки наличия пользователя в бд
async def check_user_in_db(user_id) -> bool:
    return await db.user_exists(user_id)


# Когда /start ввели
@dp.message(Command("start"))
async def start_command(message: types.Message) -> None:
    user_id = message.from_user.id
    await db.add_user(user_id)
    await message.answer("Привет! Используй /baby, чтобы получить фото.")


# Когда /baby ввели
@dp.message(Command("baby"))
async def send_baby_photo(message: types.Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username

    # Проверяем, зарегистрирован ли пользователь
    is_user_registered = await db.user_exists(user_id)
    if not is_user_registered:
        await message.reply("Вы не зарегистрированы. Пожалуйста, нажмите /start, чтобы зарегистрироваться.")
        return
    message_time = await db.when_user_can_send_message(user_id)
    if datetime.now() < datetime.fromisoformat(message_time):
        await message.reply(
            f"Остынь, @{username},\nПопробуй чуть позже, например через {(message_time - datetime.now()).seconds} сек"
            f"\n\nP.s. сократить кд можно с помощью /brutforce")
        return
    category = choose_category()
    photos_ids = await db.get_photos_from_category(category, user_id)
    photo_id = random.choice(photos_ids)[0]
    photo_path = await db.get_path(photo_id)
    if category == 1:
        await message.reply_photo(photo_path, caption = 'Поздравляю, у тебя явно есть удача\nСегодня без кд\n\n+100 babyCoin')
    elif category == 2:
        await message.reply_photo(photo_path, caption='Знаешь, могло быть и хуже, сиди учи(\nЛови кд на 60 секунд\n\n+1 babyCoin') # Придумай чет новое
    elif category == 3:
        await message.reply_photo(photo_path, caption = 'ААААА женщина\nДумаю 30 секунд тебе хватит\n\n+5 babyCoin') # Придумай чет новое
    elif category == 4:
        await message.reply_photo(photo_path, caption= 'Капец ты лохопендр\nЛови кд на 2 минуты\n\n-100 babyCoin')
    else:
        await message.answer("Ты как сюда попал?")

'''
# Нажатие на рейтинг
@dp.callback_query(MyCallback.filter())
async def vote_callback(call: types.CallbackQuery, callback_data: MyCallback) -> None:
'''



async def main() -> None:
    await on_start()
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

