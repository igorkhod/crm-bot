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
from crm2.db.users import get_user_by_tg
from crm2.keyboards.main_menu import main_menu_kb
from crm2.keyboards import guest_start_kb

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
    tg_id = message.from_user.id
    user = get_user_by_tg(tg_id)
  # В главное меню пускаем ТОЛЬКО при полном профиле
    if _profile_complete(user):
        await message.answer(
            "Главное меню (ваша роль: {role})".format(role=user.get("role", "user")),
            reply_markup = main_menu_kb(),
        )

        return

    text = (
        "Добро пожаловать в Psytech! 🧭 Здесь начинается путь из дисциплины в свободу.\n"
        "Ниже — важные шаги для запуска.\n\n"
        "У вас не завершена регистрация или вы не вошли в систему.\n"
        "Вы гость. Выберите действие:"

    )
    await message.answer(text, reply_markup=guest_start_kb())