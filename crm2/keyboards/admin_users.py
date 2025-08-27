# crm2/keyboards/admin_users.py
# Краткая аннотация: inline-клавиатуры для раздела "Пользователи" (админ-панель)

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

# Ключи групп — стабильные, на них будем вешать логику выборки
GROUPS = [
    ("1 поток", "users:group:stream_1"),
    ("2 поток", "users:group:stream_2"),
    ("Новый набор", "users:group:new_intake"),
    ("Окончившие", "users:group:alumni"),
    ("Админы", "users:group:admins"),
]

def users_groups_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for title, cb in GROUPS:
        kb.button(text=title, callback_data=cb)
    kb.button(text="⬅️ Назад в админ-панель", callback_data="admin:back")
    kb.adjust(2, 2, 1)  # 2-2-1 в ряд
    return kb.as_markup()
