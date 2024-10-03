from aiogram.filters.callback_data import CallbackData


class MyCallback(CallbackData, prefix="my"):
    rating: int
    photo_id: int
    user_id: int
