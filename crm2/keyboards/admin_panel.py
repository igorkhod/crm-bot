# crm2/keyboards/admin_panel.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_panel_kb() -> InlineKeyboardMarkup:
    """
    Главное меню админ-панели.
    Кнопки сгруппированы по блокам: пользователи, расписание, посещаемость,
    домашние задания, рассылка, логи, диагностика.
    """
    rows = [
        [
            InlineKeyboardButton(text="👥 Пользователи", callback_data="adm:users"),
            InlineKeyboardButton(text="🗓 Расписание",  callback_data="adm:schedule"),
        ],
        [
            InlineKeyboardButton(text="📋 Посещаемость",     callback_data="adm:attendance"),
            InlineKeyboardButton(text="📚 Домашние задания", callback_data="adm:homework"),
        ],
        [
            InlineKeyboardButton(text="📣 Рассылка", callback_data="adm:broadcast"),
            InlineKeyboardButton(text="🧾 Логи",     callback_data="adm:logs"),
        ],
        [
            InlineKeyboardButton(text="🩺 DB Doctor",    callback_data="adm:dbdoctor"),
            InlineKeyboardButton(text="🤖 ChatGPT",      callback_data="adm:chatgpt_status"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
