# crm2/handlers/admin_users.py
# Назначение: Обработчики подменю "Пользователи" в админ-панели с фильтрацией по группам
# Функции:
# - admin_users_entry - Входная точка раздела пользователей
# - admin_users_pick_group - Обработка выбора группы пользователей
# Обработчики:
# - admin_users_entry - Показ меню групп пользователей (когорты, новые, выпускники, админы)
# - admin_users_pick_group - Подтверждение выбора группы (заглушка для будущей пагинации)

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter

from crm2.keyboards.admin_users import users_groups_kb, users_pager_kb
from crm2.db.users_repo import count_users, list_users

router = Router(name="admin_users")

# 1) Вход в подменю "Пользователи" из админ-панели
@router.message(StateFilter(None), F.text == "👥 Пользователи")
async def admin_users_entry(message: Message):
    await message.answer(
        "Выберите интересующую вас группу:",
        reply_markup=users_groups_kb()
    )

# 2) Выбор группы (пока — только подтверждаем выбор; дальше подцепим выдачу списка)
@router.callback_query(F.data.startswith("users:group:"))
async def admin_users_pick_group(cb: CallbackQuery):
    group_key = cb.data.split(":", 2)[-1]  # cohort_1 | cohort_2 | new_intake | alumni | admins
    # На этом шаге мы лишь подтверждаем выбор и остаёмся на том же сообщении.
    # Далее сюда подключим выборку из БД и пагинацию.
    mapping = {
        "cohort_1": "1 поток",
        "cohort_2": "2 поток",
        "new_intake": "Новый набор",
        "alumni": "Окончившие",
        "admins": "Админы",
    }
    human = mapping.get(group_key, group_key)
    await cb.message.edit_text(
        f"Группа: <b>{human}</b>\n(список пользователей подключим следующим шагом)",
        reply_markup=users_groups_kb()
    )
    await cb.answer()
