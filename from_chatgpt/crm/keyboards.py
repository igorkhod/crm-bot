from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_role_keyboard(role: str = None, is_authenticated: bool = False) -> ReplyKeyboardMarkup:
    """
    Главное меню 2×2:
    Админ-панель | Информация
    Расписание   | Выйти
    """
    if is_authenticated:
        if role == "admin":
            buttons = [
                [KeyboardButton(text="Админ-панель"), KeyboardButton(text="Информация")],
                [KeyboardButton(text="Расписание"),   KeyboardButton(text="Выйти")],
            ]
        else:
            buttons = [
                [KeyboardButton(text="Информация"), KeyboardButton(text="Расписание")],
                [KeyboardButton(text="Выйти")],
            ]
    else:
        buttons = [
            [
                KeyboardButton(text="🔐 Войти"),
                KeyboardButton(text="🆕 Зарегистрироваться")
            ]
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

