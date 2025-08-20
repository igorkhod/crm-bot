# crm2/routers/start.py

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from crm2.db.sqlite import get_db_connection

router = Router()

#
# def get_db_connection():
#     return sqlite3.connect("crm2.db")


def get_user_role(telegram_id: int) -> str | None:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE telegram_id=?", (telegram_id,))
        row = cur.fetchone()
        return row[0] if row else None


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    role = get_user_role(message.from_user.id)

    if role is None:  # новичок, не зарегистрирован
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🆕 Зарегистрироваться")],
                [KeyboardButton(text="🔑 Войти")],
                [KeyboardButton(text="ℹ Информация")]
            ],
            resize_keyboard=True
        )
        await message.answer("Добро пожаловать! 👋\nВыберите действие:", reply_markup=kb)

    elif role == "user":
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Расписание")],
                [KeyboardButton(text="📚 Материалы")],
                [KeyboardButton(text="ℹ Информация")]
            ],
            resize_keyboard=True
        )
        await message.answer("Добро пожаловать обратно, курсант 🎓", reply_markup=kb)

    elif role == "advanced_user":
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📰 Новости психонетики")],
                [KeyboardButton(text="📚 Новые технологии")]
            ],
            resize_keyboard=True
        )
        await message.answer("Добро пожаловать, выпускник 🌟", reply_markup=kb)

    elif role == "admin":
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⚙ Админ-панель")],
                [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="ℹ Информация")]
            ],
            resize_keyboard=True
        )
        await message.answer("Здравствуйте, администратор 🔑", reply_markup=kb)

    else:
        await message.answer("⚠️ Неизвестная роль, обратитесь к администратору.")
