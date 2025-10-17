from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from crm2.services.users import get_user_by_telegram, set_user_cohort, get_cohorts

# crm2/handlers/profile.py
# Назначение: Личный кабинет пользователя с настройками профиля и управлением потоком
# Функции:
# - _extract_ids - Универсальное извлечение chat_id и user_id из Message/CallbackQuery
# - _profile_kb - Создание клавиатуры личного кабинета
# - show_profile - Универсальный показ профиля (поддерживает Message и CallbackQuery)
# Обработчики:
# - profile_entry - Вход в личный кабинет по кнопке
# - ask_stream - Интерфейс выбора учебного потока
# - set_stream_cb - Сохранение выбранного потока в БД
# - profile_back - Возврат в карточку профиля
# - profile_back_main - Возврат в главное меню с удалением сообщения
# - toggle_notify - Переключение настроек уведомлений
# ... твои импорт(ы) БД/сервисов остаются как есть ...
# новое описание
# crm2/handlers/profile.py
# Назначение: Личный кабинет пользователя с настройками профиля и управлением потоком
# Функции:
# - _extract_ids - Универсальное извлечение chat_id и user_id из Message/CallbackQuery
# - _profile_kb - Создание клавиатуры личного кабинета
# - show_profile - Универсальный показ профиля (поддерживает Message и CallbackQuery)
# Обработчики:
# - profile_entry - Вход в личный кабинет по кнопке
# - ask_stream - Интерфейс выбора учебного потока
# - set_stream_cb - Сохранение выбранного потока в БД
# - profile_back - Возврат в карточку профиля
# - profile_back_main - Возврат в главное меню с удалением сообщения
# - toggle_notify - Переключение настроек уведомлений

router = Router()

# ----------------------------------------------------------------------
# Универсальные помощники

def _extract_ids(obj: Message | CallbackQuery) -> tuple[int, int]:
    """
    Возвращает (chat_id, user_id) для Message или CallbackQuery.
    Никогда не создаёт «поддельные» Message.
    """
    if isinstance(obj, CallbackQuery):
        chat_id = obj.message.chat.id
        user_id = obj.from_user.id
    else:
        chat_id = obj.chat.id
        user_id = obj.from_user.id
    return chat_id, user_id


def _profile_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="🧭 Установить/изменить поток", callback_data="profile:set_stream")
    kb.button(text="🔔 Уведомления: вкл/выкл", callback_data="profile:toggle_notify")
    kb.button(text="🏠 В главное меню", callback_data="profile:back_main")
    kb.adjust(1, 1, 1)
    return kb
# ----------------------------------------------------------------------


@router.message(F.text == "👤 Личный кабинет")
async def profile_entry(message: Message):
    await show_profile(message)


async def show_profile(obj: Message | CallbackQuery):
    chat_id, tg_id = _extract_ids(obj)

    # Получаем данные пользователя из БД
    user = await get_user_by_telegram(tg_id)

    if not user:
        text = "❌ Пользователь не найден. Пройдите регистрацию."
        if isinstance(obj, CallbackQuery):
            await obj.message.edit_text(text)
        else:
            await obj.answer(text)
        return

    # Формируем информацию о потоке
    cohort_info = "❌ Не установлен"
    if user.get('cohort_id'):
        # Получаем название потока
        cohorts = await get_cohorts()
        cohort_name = next((c['name'] for c in cohorts if c['id'] == user['cohort_id']), f"Поток {user['cohort_id']}")
        cohort_info = f"{cohort_name}"

    # Форматируем дату регистрации
    created_at = user.get('created_at', 'Неизвестно')
    if created_at and created_at != 'Неизвестно':
        try:
            # Преобразуем SQLite datetime в читаемый формат
            from datetime import datetime
            # Парсим дату из формата '2025-10-15 10:59:43'
            dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            created_at = dt.strftime('%d.%m.%Y в %H:%M')
        except Exception as e:
            # Если не удалось распарсить, оставляем как есть
            logging.debug(f"Could not parse date {created_at}: {e}")

    text = (
        "👤 *Личный кабинет*\n\n"
        f"🆔 TG ID: `{tg_id}`\n"
        f"👤 Логин: {user.get('nickname', 'Не указан')}\n"
        f"📛 Полное имя: {user.get('full_name', 'Не указано')}\n"
        f"📧 Email: {user.get('email', 'Не указан')}\n"
        f"📞 Телефон: {user.get('phone', 'Не указан')}\n"
        f"🧭 Поток: {cohort_info}\n"
        f"🎭 Роль: {user.get('role', 'user')}\n"
        f"📅 Зарегистрирован: {created_at}\n"
        "\nВы можете установить или изменить свой поток обучения."
    )

    # if isinstance(obj, CallbackQuery):
    #     await obj.message.edit_text(text, reply_markup=_profile_kb().as_markup(), parse_mode="Markdown")
    #     await obj.answer()
    # else:
    #     await obj.answer(text, reply_markup=_profile_kb().as_markup(), parse_mode="Markdown")
    if isinstance(obj, CallbackQuery):
        await obj.message.edit_text(text, reply_markup=_profile_kb().as_markup())
        await obj.answer()
    else:
        await obj.answer(text, reply_markup=_profile_kb().as_markup())

# =======================
# Установка потока
# =======================

@router.callback_query(F.data == "profile:set_stream")
async def ask_stream(cq: CallbackQuery):
    # Получаем список потоков из БД
    cohorts = await get_cohorts()

    if not cohorts:
        await cq.answer("❌ Нет доступных потоков", show_alert=True)
        return

    kb = InlineKeyboardBuilder()

    # Добавляем кнопки для каждого потока
    for cohort in cohorts:
        kb.button(text=f"🧭 {cohort['name']}", callback_data=f"profile:set_stream:{cohort['id']}")

    kb.button(text="⬅️ Назад", callback_data="profile:back")
    kb.adjust(1)  # По одной кнопке в ряд

    await cq.message.edit_text(
        "🎯 *Выберите ваш учебный поток:*\n\n"
        "• 09.2023 - Поток сентября 2023\n"
        "• 04.2025 - Поток апреля 2025",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await cq.answer()


@router.callback_query(F.data.startswith("profile:set_stream:"))
async def set_stream_cb(cq: CallbackQuery):
    try:
        cohort_id = int(cq.data.split(":")[-1])
    except Exception:
        logging.exception("[PROFILE] Некорректный cohort_id")
        await cq.answer("❌ Некорректный поток", show_alert=True)
        return

    _, tg_id = _extract_ids(cq)

    # Сохраняем поток в БД
    success = await set_user_cohort(tg_id, cohort_id)

    if success:
        # Получаем название потока для сообщения
        cohorts = await get_cohorts()
        cohort_name = next((c['name'] for c in cohorts if c['id'] == cohort_id), f"Поток {cohort_id}")

        await cq.answer(f"✅ Поток '{cohort_name}' сохранён!")
        await show_profile(cq)
    else:
        await cq.answer("❌ Ошибка сохранения потока", show_alert=True)


# Остальные обработчики остаются без изменений...
@router.callback_query(F.data == "profile:back")
async def profile_back(cq: CallbackQuery):
    await show_profile(cq)


@router.callback_query(F.data == "profile:back_main")
async def profile_back_main(cq: CallbackQuery):
    from crm2.keyboards import main_menu_kb
    await cq.message.delete()
    await cq.message.answer("Меню:", reply_markup=main_menu_kb())
    await cq.answer()


@router.callback_query(F.data == "profile:toggle_notify")
async def toggle_notify(cq: CallbackQuery):
    # TODO: Реализовать переключение уведомлений
    await cq.answer("🔔 Функция уведомлений в разработке")
    await show_profile(cq)
