# crm2/keyboards/admin_panel.py
# Назначение: Reply-клавиатура админ-панели с навигацией по всем разделам
# Функции:
# - admin_panel_kb - Основная клавиатура админ-панели с 8 разделами управления
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def admin_panel_kb() -> ReplyKeyboardMarkup:
    """
    Админ-панель как ReplyKeyboard.
    Тексты кнопок совпадают с тем, что ловят хендлеры по F.text
    (например: "📋 Посещаемость", "📚 Домашние задания").
    """
    rows = [
        [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="📅 Расписание")],
        [KeyboardButton(text="📋 Посещаемость"), KeyboardButton(text="📚 Домашние задания")],
        [KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="🧾 Логи")],
        [KeyboardButton(text="🩺 DB Doctor"), KeyboardButton(text="🧠 ChatGPT")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
        is_persistent=True,
    )
