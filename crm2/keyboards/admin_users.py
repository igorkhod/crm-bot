# crm2/keyboards/admin_users.py
# Назначение: Inline-клавиатуры для раздела пользователей в админ-панели
# Функции:
# - users_groups_kb - Клавиатура выбора групп пользователей (когорты, новые, выпускники, админы)
# - users_pager_kb - Клавиатура пагинации для списка пользователей группы

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

GROUPS = [
    ("1 поток", "users:group:cohort_1"),
    ("2 поток", "users:group:cohort_2"),
    ("Новый набор", "users:group:new_intake"),
    ("Окончившие", "users:group:alumni"),
    ("Админы", "users:group:admins"),
]


def users_groups_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for title, cb in GROUPS:
        kb.button(text=title, callback_data=cb)
    kb.button(text="⬅️ Назад в админ-панель", callback_data="admin:back")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def users_pager_kb(group_key: str, page: int, pages: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    prev_p = max(1, page - 1)
    next_p = min(pages, page + 1)
    kb.button(text="◀️", callback_data=f"users:page:{group_key}:{prev_p}")
    kb.button(text=f"{page}/{pages}", callback_data="noop")
    kb.button(text="▶️", callback_data=f"users:page:{group_key}:{next_p}")
    kb.button(text="🔄 Выбрать группу", callback_data="users:groups")
    kb.button(text="⬅️ Назад в админ-панель", callback_data="admin:back")
    kb.adjust(3, 2)
    return kb.as_markup()
