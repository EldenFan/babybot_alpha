from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup

class PhotoCallback(CallbackData, prefix="ph"):
    rating: int
    photo_id: int

class PackageCallback(CallbackData, prefix="pa"):
    action: str
    package_id: int
    photo_id: int

class PackageStates(StatesGroup):
    waiting_for_package_name = State()
    waiting_for_photos = State()
    choosing_package_to_edit = State()
    editing_package = State()
    waiting_for_photo_to_remove = State()
