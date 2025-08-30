import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import asyncio
import db
import stringResources
from config import TOKEN, ADMINS_ID
from myClass import PhotoCallback, PackageCallback, PackageStates
import os
from datetime import datetime
from aiogram import F
from aiogram.filters import Command, StateFilter

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
    await message.answer(stringResources.START_STRING)


# Когда /baby ввели
@dp.message(Command("baby"))
async def send_baby_photo(message: types.Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username

    is_user_registered = await db.user_exists(user_id)
    if not is_user_registered:
        await message.reply(stringResources.NO_USER_IN_BD_STRING)
        return
    
    message_time = await db.when_user_can_send_message(user_id)
    if (message_time is not None and datetime.now() < datetime.fromisoformat(message_time)):
        await message.reply(stringResources.generate_early_message(username, (message_time - datetime.now()).seconds))
        return
    
    category = choose_category()
    photos_ids = await db.get_photos_from_category(category, user_id)
    caption = await db.get_text_from_category()
    photo_id = random.choice(photos_ids)[0]
    photo_path = await db.get_path(photo_id)
    await message.reply_photo(photo_path, caption = caption)


@dp.message(Command("AddPackage"))
async def add_package(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id

    if not await isAdmin(message, user_id):
        return
    
    await message.answer(stringResources.SET_PACKAGE_NAME_STRING)
    await state.set_state(PackageStates.waiting_for_package_name)
    

@dp.message(PackageStates.waiting_for_package_name)
async def process_package_name(message: types.Message, state: FSMContext) -> None:
    package_name = message.text
    package_id = await db.create_package(package_name)
    
    await state.update_data(package_id=package_id)
    await message.answer(stringResources.package_created_string(package_name))
    await state.set_state(PackageStates.waiting_for_photos)


@dp.message(PackageStates.waiting_for_photos, F.content_type == types.ContentType.PHOTO)
async def process_package_photos(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    package_id = data['package_id']
    
    photo = message.photo[-1]
    file_id = photo.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    
    filename = f"photos/{package_id}_{file_id}.jpg"
    await message.bot.download_file(file_path, filename)
    
    await db.add_photo_to_package(filename, package_id)
    
    await message.answer(stringResources.GET_PHOTO_FOR_PACKAGE_STRING)


@dp.message(Command("done"), PackageStates.waiting_for_photos)
async def finish_adding_photos(message: types.Message, state: FSMContext) -> None:
    await message.answer(stringResources.PACKAGE_CREATED_STRING)
    await state.clear()


@dp.message(Command("ChangePackage"))
async def change_package(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id

    if not await isAdmin(message, user_id):
        return
    
    keyboard = await create_packages_keyboard()
    await message.answer(stringResources.CHOOSE_PACKAGE_FOR_CHANGE, reply_markup=keyboard)
    await state.set_state(PackageStates.choosing_package_to_edit)

@dp.callback_query(PackageStates.choosing_package_to_edit, PackageCallback.filter(F.action == "edit_package"))
async def process_package_selection(callback_query: types.CallbackQuery, callback_data: PackageCallback, state: FSMContext) -> None:
    package_id = callback_data.package_id
    await state.update_data(package_id=package_id)
    
    package_name = await db.get_package_name(package_id)
    photos = await db.get_photos_in_package(package_id)
    
    await callback_query.message.edit_text(
        stringResources.change_package_string(package_name, photos),
        reply_markup = create_packages_keyboard()
    )

    await state.set_state(PackageStates.editing_package)

@dp.callback_query(PackageStates.editing_package, PackageCallback.filter(F.action =="add_photo"))
async def add_photo_to_existing_package(callback_query: types.CallbackQuery, callback_data: PackageCallback, state: FSMContext) -> None:
    package_id = callback_data.package_id
    await state.update_data(package_id=package_id)
    
    package_name = await db.get_package_name(package_id)
    await callback_query.message.answer(stringResources.package_adding_string(package_name))
    await state.set_state(PackageStates.waiting_for_photos)

# Обработчик удаления фото из пакета
@dp.callback_query(PackageStates.editing_package, PackageCallback.filter(F.action =="remove_photo"))
async def remove_photo_from_package(callback_query: types.CallbackQuery, callback_data: PackageCallback, state: FSMContext) -> None:
    package_id = callback_data.package_id
    photos = await db.get_photos_in_package(package_id)
    
    keyboard = []
    for photo in photos:
        keyboard.append([InlineKeyboardButton(
            text=stringResources.DELETE_STRING,
            callback_data=PackageCallback(action="delete_photo", photo_id=photo[0], package_id=package_id).pack()
        )])
    
    keyboard.append([InlineKeyboardButton(
        text=stringResources.RETURN_STRING,
        callback_data=PackageCallback(action="back_to_editing", package_id=package_id).pack()
    )])
    
    await callback_query.message.edit_text(
        stringResources.CHOOSE_PHOTO_TO_DELETE_STRING,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(PackageStates.waiting_for_photo_to_remove)

# Обработчик удаления конкретного фото
@dp.callback_query(PackageStates.waiting_for_photo_to_remove, PackageCallback.filter(F.action =="delete_photo"))
async def process_photo_deletion(callback_query: types.CallbackQuery, callback_data: PackageCallback, state: FSMContext) -> None:
    photo_id = callback_data.photo_id
    package_id = callback_data.package_id
    await db.remove_photo_from_package(photo_id)
    
    await callback_query.message.answer(stringResources.DELETE_PHOTO_STRING)
    
    package_name = await db.get_package_name(package_id)
    photos = await db.get_photos_in_package(package_id)
    
    await callback_query.message.edit_text(
        stringResources.change_package_string(package_name, photos),
        reply_markup = create_packages_keyboard()
    )
    await state.set_state(PackageStates.editing_package)

# Обработчик завершения редактирования
@dp.callback_query(PackageStates.editing_package, PackageCallback.filter(F.action == "finish_editing"))
async def finish_editing_package(callback_query: types.CallbackQuery, callback_data: PackageCallback, state: FSMContext) -> None:
    await callback_query.message.edit_text(stringResources.changed_package_string())
    await state.clear()
    
    
# Создание клавиатуры из пакетов
async def create_packages_keyboard() -> InlineKeyboardMarkup:
    packages = await db.get_all_packages()
    keyboard = []
    for package in packages:
        keyboard.append([InlineKeyboardButton(
            text=package[1], 
            callback_data=PackageCallback(action="edit_package", package_id=package[0]).pack()
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Проверка на админа
async def isAdmin(message, user_id) -> bool:
     if user_id not in ADMINS_ID:
        await message.reply(stringResources.NOT_ADMIN_STRING)
        return False
     return True

# Создание клавиатуры изменения пакетов
def create_change_package_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=stringResources.ADD_PHOTO_STRING, callback_data=PackageCallback(action="add_photo", package_id=package_id).pack())],
        [InlineKeyboardButton(text=stringResources.DELETE_PHOTO_STRING, callback_data=PackageCallback(action="remove_photo", package_id=package_id).pack())],
        [InlineKeyboardButton(text=stringResources.STOP_CHANGING_STRING, callback_data=PackageCallback(action="finish_editing", package_id=package_id).pack())]
    ])

async def main() -> None:
    await on_start()
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

