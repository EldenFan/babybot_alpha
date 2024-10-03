import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm import State, StatesGroup
import asyncio
import db
from config import TOKEN
from myClass import MyCallback
import os

dp = Dispatcher()

# Словарь с вероятностями дропа категорий
categories = {
    'good': 0.05,
    'rare good': 0.45,
    'rare bad': 0.45,
    'bad': 0.05
}

# Выбор категории
def choose_category() -> str:
    categories_list = list(categories.keys())
    probabilities = list(categories.values())
    return random.choices(categories_list, probabilities)[0]


# Создать бд, если её нет
async def on_start() -> None:
    os.makedirs('photos', exist_ok=True)
    await db.init()


# Функция проверки наличия пользователя в бд
async def check_user_in_db(user_id) -> tuple:
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

    # Проверяем, зарегистрирован ли пользователь
    is_user_registered = await db.user_exists(user_id)
    if not is_user_registered:
        await message.answer("Вы не зарегистрированы. Пожалуйста, нажмите /start, чтобы зарегистрироваться.")
        return

    category = choose_category()
    photo_data = await db.get_random(category)

    # Проверка выдали нам фото (Если уверен убери сам if, но оставь саму логику внутри if, и все else)
    if photo_data:
        photo_id, category, photo_path, rating, votes = photo_data

        caption = f"Категория: {category}\nСредний рейтинг: {rating:.2f} (Голосов: {votes})"

        markup = InlineKeyboardMarkup()
        for i in range(1, 6):
            markup.add(InlineKeyboardButton(
                str(i),
                callback_data=MyCallback(rating=i, photo_id=photo_id, user_id=user_id)
            ))

        with open(photo_path, 'rb') as photo:
            await message.answer_photo(photo, caption=caption, reply_markup=markup)
    else:
        await message.answer("Фото в этой категории не найдено.")


# Нажатие на рейтинг
@dp.callback_query(MyCallback.filter())
async def vote_callback(call: types.CallbackQuery, callback_data: MyCallback) -> None:
    user_id = call.from_user.id
    rating = int(callback_data.rating)
    photo_id = int(callback_data.photo_id)
    original_user_id = int(callback_data.user_id)

    # Проверка, совпадает ли ID пользователя, который пытается проголосовать, с тем, кому показывалось фото
    if user_id != original_user_id:
        await call.answer("Вы не можете голосовать за это фото, так как оно было показано другому пользователю.",
                          show_alert=True)
        return

    # Добавляем голос
    await db.add_vote(user_id, photo_id, rating)

    # Получаем обновленный рейтинг и количество голосов
    updated_rating, updated_votes = await db.get_photo_rating(photo_id)

    # Ответ пользователю с новым рейтингом
    await call.answer(f"Спасибо за ваш голос! Новый рейтинг: {updated_rating:.2f} (Голосов: {updated_votes})")


async def main() -> None:
    await on_start()
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

