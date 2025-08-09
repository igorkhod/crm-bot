from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_role_keyboard(role: str = None, is_authenticated: bool = False) -> ReplyKeyboardMarkup:
    if is_authenticated:
        if role == "admin":
            buttons = [
                [KeyboardButton(text="Админ-панель")],
                [KeyboardButton(text="Информация")]
            ]
        elif role == "participant":
            buttons = [
                [KeyboardButton(text="Информация")]
            ]
        else:
            buttons = [
                [KeyboardButton(text="Информация")]
            ]
    else:
        buttons = [
            [KeyboardButton(text="🔐 Войти")],
            [KeyboardButton(text="🆕 Зарегистрироваться")]
        ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
