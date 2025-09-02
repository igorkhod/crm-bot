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



# def guest_menu_kb() -> InlineKeyboardBuilder:
#     kb = InlineKeyboardBuilder()
#     kb.button(text="🔐 Войти", callback_data="login:start")
#     kb.button(text="📝 Зарегистрироваться", callback_data=REG_START)  # <-- единый ключ
#     kb.button(text="📄 О проекте", callback_data="about:project")
#     kb.adjust(2, 1)
#     return kb


@router.message(F.text == "/start")
async def cmd_start(message: Message) -> None:
    # """Разводим новых и существующих пользователей:
    #    - новые → гостевое меню
    #    - зарегистрированные → сразу в главное меню."""
    tg_id = message.from_user.id
    user = get_user_by_tg(tg_id)

    if user and (user.get("role") or "user") != "guest":
        # Уже есть в БД → отправляем в главное меню
        await message.answer("Главное меню (ваша роль: {role})".format(role=user.get("role", "user")),
                             reply_markup=main_menu_kb())
        return

    # Гость / новый пользователь → приветствие + явная подсказка
    text = (
        "Добро пожаловать в Psytech! 🧭 Здесь начинается путь из дисциплины в свободу.\n"
        "Ниже — важные шаги для запуска.\n\n"
        "Вы гость. Выберите действие:"
    )
    await message.answer(text, reply_markup=guest_start_kb())