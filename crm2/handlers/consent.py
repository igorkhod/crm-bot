# crm2/handlers/consent.py
from __future__ import annotations

import sqlite3
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

router = Router(name="consent")


def get_db_connection():
    """Получение соединения с БД"""
    db_path = Path(__file__).resolve().parent.parent / "data" / "crm.db"
    return sqlite3.connect(db_path)


@router.message(F.text.func(lambda t: t and t.lower() in {"согласие", "даю согласие", "consent"}))
@router.callback_query(F.data == "accept_consent")
async def accept_consent(update: Message | CallbackQuery):
    """Обработчик согласия пользователя с записью в БД"""
    user_id = update.from_user.id

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Обновляем флаг согласия в базе
        cursor.execute(
            "UPDATE users SET consent_given = 1, consent_date = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (user_id,)
        )

        if cursor.rowcount > 0:
            conn.commit()
            success_text = "✅ Ваше согласие на обработку персональных данных зафиксировано."
        else:
            success_text = "❌ Пользователь не найден. Пожалуйста, завершите регистрацию."

        conn.close()

    except Exception as e:
        success_text = "⚠️ Произошла ошибка при сохранении согласия."
        print(f"Database error: {e}")

    # Отправляем ответ
    if isinstance(update, CallbackQuery):
        await update.message.answer(success_text)
        await update.answer()
    else:
        await update.answer(success_text)


@router.message(Command("consent"))
async def consent_info(message: Message):
    """Информация о согласии по команде /consent"""
    await message.answer(
        "📋 **Согласие на обработку персональных данных**\n\n"
        "Для работы с системой Psytech CRM необходимо ваше согласие "
        "на обработку персональных данных в соответствии с политикой конфиденциальности.\n\n"
        "Нажмите кнопку ниже или напишите 'Согласие' для подтверждения.",
        reply_markup=create_consent_keyboard()
    )


def create_consent_keyboard():
    """Создает клавиатуру для согласия"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Даю согласие", callback_data="accept_consent")
        ]]
    )
