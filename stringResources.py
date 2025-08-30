START_STRING = "Привет! Используй /baby, чтобы получить фото."
NO_USER_IN_BD_STRING = "Вы не зарегистрированы. Пожалуйста, нажмите /start, чтобы зарегистрироваться."
NOT_ADMIN_STRING = "Вы не администратор, вам нельзя пользоваться данной функцией"
SET_PACKAGE_NAME_STRING = "Введите название нового пакета:"
GET_PHOTO_FOR_PACKAGE_STRING = "Фото добавлено в пакет. Отправьте еще фото или нажмите /done чтобы завершить."
PACKAGE_CREATED_STRING = "Пакет создан."
CHOOSE_PACKAGE_FOR_CHANGE_STRING = "Выберите пакет для редактирования:"
ADD_PHOTO_STRING = "Добавить фото"
DELETE_PHOTO_STRING = "Удалить фото"
DELETED_PHOTO_STRING = "Фото удалено"
STOP_CHANGING_STRING = "Завершить редактирование"
DELETE_STRING = "Удалить"
RETURN_STRING = "Назад"
CHOOSE_PHOTO_TO_DELETE_STRING = "Выберите фото для удаления:"


def generate_early_message(username: str, delay):
    return f"Остынь, @{username},\nПопробуй чуть позже, например через {delay} сек\n\nP.s. сократить кд можно с помощью /brutforce"


def change_package_string(name: str, count: int):
    f"Редактирование пакета: {name}\nКоличество фото: {count}"

def package_created_string(name: str):
    return f"Отправьте фотографии для пакета {name}."


def package_adding_string(name: str):
    return f"Отправьте фото для добавления в пакет '{name}':"

def changed_package_string(name: str, count: int):
    f"Редактирование пакета: {name}\nКоличество фото: {count} завершено"