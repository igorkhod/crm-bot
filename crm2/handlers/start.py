# === Автогенерированный заголовок: crm2/handlers/start.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: guest_menu_kb, cmd_start
# === Конец автозаголовка
# crm2/handlers/start.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from crm2.keyboards import guest_start_kb
from crm2.db.users import get_user_by_tg  # можно оставить, но больше не используем для ветвления


router = Router()


# Профиль считаем завершённым, если заполнены nickname и password.
def _profile_complete(u: dict | None) -> bool:
    if not u:
        return False
    nick = (u.get("nickname") or "").strip()
    pwd  = (u.get("password") or "").strip()
    return bool(nick and pwd)


@router.message(F.text == "/start")
async def cmd_start(message: Message) -> None:
    """/start всегда ведёт в гостевой режим: вход или регистрация."""
    # над меню — инлайн-кнопка «Исправить регистрацию»
    kb = InlineKeyboardBuilder()
    kb.button(text="🧰 Исправить регистрацию", callback_data="reg:review")
    await message.answer(
        "Добро пожаловать в Psytech! 🧭 Здесь начинается путь из дисциплины в свободу.\n"
        "Ниже — важные шаги для запуска.\n\n"
        "Если допустили ошибку при регистрации — исправьте её:",
        reply_markup=kb.as_markup(),
    )
    # само гостевое меню — reply-клавиатура
    await message.answer("Выберите действие:", reply_markup=guest_start_kb())
