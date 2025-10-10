# crm2/handlers/profile.py
from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ... твои импорт(ы) БД/сервисов остаются как есть ...

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
    kb.button(text="🛠 Установить поток", callback_data="profile:set_stream")
    kb.button(text="🔔 Уведомления: вкл/выкл", callback_data="profile:toggle_notify")
    kb.button(text="🏠 В главное меню", callback_data="profile:back_main")
    kb.adjust(1, 1, 1)
    return kb
# ----------------------------------------------------------------------


@router.message(F.text == "👤 Личный кабинет")
async def profile_entry(message: Message):
    await show_profile(message)


async def show_profile(obj: Message | CallbackQuery):
    """
    Показывает карточку профиля. Теперь принимает и Message, и CallbackQuery.
    """
    chat_id, tg_id = _extract_ids(obj)

    # --- тут твоя логика загрузки пользователя/статистики ---
    # пример:
    # user = get_user_by_telegram(tg_id)
    # next_lesson = ...
    # attendance_stats = ...

    text = (
        "👤 *Личный кабинет*\n\n"
        f"TG ID: `{tg_id}`\n"
        # Дополни данными из БД:
        # f"ФИО: {user.full_name}\n"
        # f"Роль: {user.role}\n"
        # f"Поток: {stream_title}\n"
        # f"Ближайшее занятие: {next_lesson}\n"
        "\nВы можете установить/изменить свой поток."
    )

    # Отвечаем в зависимости от источника
    if isinstance(obj, CallbackQuery):
        # При коллбэке корректно редактировать *предыдущее* сообщение
        await obj.message.edit_text(text, reply_markup=_profile_kb().as_markup(), parse_mode="Markdown")
        await obj.answer()
    else:
        await obj.answer(text, reply_markup=_profile_kb().as_markup(), parse_mode="Markdown")


# =======================
# Установка потока
# =======================

@router.callback_query(F.data == "profile:set_stream")
async def ask_stream(cq: CallbackQuery):
    # Покажи выбор потоков (пример на двух потоках)
    kb = InlineKeyboardBuilder()
    kb.button(text="Поток 1", callback_data="profile:set_stream:1")
    kb.button(text="Поток 2", callback_data="profile:set_stream:2")
    kb.button(text="⬅️ Назад", callback_data="profile:back")
    kb.adjust(2, 1)
    await cq.message.edit_text("Выберите свой поток:", reply_markup=kb.as_markup())
    await cq.answer()


@router.callback_query(F.data.startswith("profile:set_stream:"))
async def set_stream_cb(cq: CallbackQuery):
    # Получаем выбранный поток из callback_data
    try:
        stream_id = int(cq.data.split(":")[-1])
    except Exception:
        logging.exception("[PROFILE] Некорректный stream_id в callback_data=%r", cq.data)
        await cq.answer("Некорректный поток", show_alert=True)
        return

    # chat_id/tg_id реальны — берём напрямую из CallbackQuery
    _, tg_id = _extract_ids(cq)

    # --- тут сохрани stream_id в БД для пользователя tg_id ---
    # пример:
    # user = get_user_by_telegram(tg_id)
    # update_user_stream(user.id, stream_id)

    await cq.answer("Поток сохранён 👍")
    # И просто показываем профиль заново (без «поддельных» Message):
    await show_profile(cq)


@router.callback_query(F.data == "profile:back")
async def profile_back(cq: CallbackQuery):
    await show_profile(cq)


@router.callback_query(F.data == "profile:back_main")
async def profile_back_main(cq: CallbackQuery):
    # если у тебя есть клавиатура главного меню — подставь её
    from crm2.keyboards import main_menu_kb  # пример импорта
    # СТАЛО:
    # Удалите старое сообщение и отправьте новое
    await cq.message.delete()
    await cq.message.answer("Меню:", reply_markup=main_menu_kb())
    await cq.answer()


@router.callback_query(F.data == "profile:toggle_notify")
async def toggle_notify(cq: CallbackQuery):
    # переключи флаг в БД ...
    await cq.answer("Готово")
    await show_profile(cq)
