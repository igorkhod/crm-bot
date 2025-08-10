import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import requests

# -----------------------------------------------------
# Загрузка токена
# -----------------------------------------------------
local_env = Path(__file__).parent / "token_local.env"
if local_env.exists():
    load_dotenv(local_env)
    ENVIRONMENT = "LOCAL"
    print(f"Использую секреты: {local_env}")
else:
    load_dotenv("/etc/secrets/token.env")
    ENVIRONMENT = "RENDER"
    print("Использую секреты: /etc/secrets/token.env")

TOKEN = os.getenv("TELEGRAM_TOKEN")
print(f"Режим запуска: {ENVIRONMENT}")

# -----------------------------------------------------
# Логирование
# -----------------------------------------------------
logging.basicConfig(level=logging.INFO)

# Валюты и эмодзи
CURRENCIES = ["RUB", "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]
CURRENCY_EMOJIS = {
    "USD": "💵", "EUR": "💶", "RUB": "💴", "GBP": "💷",
    "JPY": "💴", "CHF": "💰", "AUD": "🦘", "CAD": "🍁", "NZD": "🐑"
}

# -----------------------------------------------------
# Инициализация
# -----------------------------------------------------
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_state = {}  # состояние пользователя

# -----------------------------------------------------
# Логгер всех обновлений
# -----------------------------------------------------
@dp.update()
async def log_all_updates(update: types.Update):
    print("⬇️ ПОЛУЧЕНО ОБНОВЛЕНИЕ:")
    print(update.model_dump_json(indent=2))

# -----------------------------------------------------
# Курсы валют
# -----------------------------------------------------
def get_rate(base: str, symbol: str) -> float:
    url = f"https://open.er-api.com/v6/latest/{base}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        return data["rates"].get(symbol, 1)
    except Exception:
        return 1

def emoji(cur: str) -> str:
    return CURRENCY_EMOJIS.get(cur, "")

def format_value(user_id):
    st = user_state.setdefault(user_id, {"from": "USD", "to": "RUB", "amount_str": ""})
    from_cur = st["from"]
    to_cur = st["to"]
    try:
        amount = float(st["amount_str"])
    except ValueError:
        amount = 0
    rate = get_rate(from_cur, to_cur)
    converted = round(amount * rate, 2)
    return f"{st['amount_str']} {emoji(from_cur)}{from_cur} = {emoji(to_cur)}{converted} {to_cur}"

# -----------------------------------------------------
# Клавиатуры
# -----------------------------------------------------
def main_calculator_kb(user_id: int) -> InlineKeyboardMarkup:
    st = user_state.get(user_id, {"from": "USD", "to": "RUB"})
    buttons = []

    buttons.append([
        InlineKeyboardButton(text=f"{emoji(st['from'])} {st['from']}", callback_data="choose_from"),
        InlineKeyboardButton(text="⇄", callback_data="swap"),
        InlineKeyboardButton(text=f"{emoji(st['to'])} {st['to']}", callback_data="choose_to"),
    ])

    layout = [
        ["7", "8", "9"],
        ["4", "5", "6"],
        ["1", "2", "3"],
        ["0", ".", "C"]
    ]
    for row in layout:
        buttons.append([
            InlineKeyboardButton(text=x, callback_data=f"digit:{x}") for x in row
        ])

    buttons.append([
        InlineKeyboardButton(text="Выйти", callback_data="exit")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def currency_keyboard(prefix: str):
    kb = InlineKeyboardBuilder()
    for cur in CURRENCIES:
        kb.button(text=f"{emoji(cur)} {cur}", callback_data=f"{prefix}:{cur}")
    kb.adjust(3)
    kb.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_calc"))
    return kb.as_markup()

# -----------------------------------------------------
# Хендлеры
# -----------------------------------------------------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_state[message.from_user.id] = {"from": "USD", "to": "RUB", "amount_str": ""}
    await message.answer(
        "Калькулятор валют\n\n" + format_value(message.from_user.id),
        reply_markup=main_calculator_kb(message.from_user.id)
    )

@dp.callback_query(F.data == "exit")
async def exit_calculator(callback: CallbackQuery):
    user_state.pop(callback.from_user.id, None)
    await callback.answer()
    await callback.message.edit_text("Вы вышли из валютного калькулятора.")

@dp.callback_query(F.data == "choose_from")
async def choose_from(callback: CallbackQuery):
    await callback.message.edit_text("Выберите исходную валюту:", reply_markup=currency_keyboard("from"))

@dp.callback_query(F.data == "choose_to")
async def choose_to(callback: CallbackQuery):
    await callback.message.edit_text("Выберите целевую валюту:", reply_markup=currency_keyboard("to"))

@dp.callback_query(F.data == "back_to_calc")
async def back_to_calculator(callback: CallbackQuery):
    await callback.message.edit_text(
        format_value(callback.from_user.id),
        reply_markup=main_calculator_kb(callback.from_user.id)
    )

@dp.callback_query(F.data == "swap")
async def swap_currencies(callback: CallbackQuery):
    st = user_state.setdefault(callback.from_user.id, {"from": "USD", "to": "RUB", "amount_str": ""})
    st["from"], st["to"] = st["to"], st["from"]
    await callback.answer("🔄 Валюты поменялись местами")
    await callback.message.edit_text(
        format_value(callback.from_user.id),
        reply_markup=main_calculator_kb(callback.from_user.id)
    )

@dp.callback_query(F.data.startswith("from:"))
async def set_from_currency(callback: CallbackQuery):
    cur = callback.data.split(":")[1]
    user_state.setdefault(callback.from_user.id, {})["from"] = cur
    await callback.message.edit_text(
        "✅ Исходная валюта выбрана\n\n" + format_value(callback.from_user.id),
        reply_markup=main_calculator_kb(callback.from_user.id)
    )

@dp.callback_query(F.data.startswith("to:"))
async def set_to_currency(callback: CallbackQuery):
    cur = callback.data.split(":")[1]
    user_state.setdefault(callback.from_user.id, {})["to"] = cur
    await callback.message.edit_text(
        "✅ Целевая валюта выбрана\n\n" + format_value(callback.from_user.id),
        reply_markup=main_calculator_kb(callback.from_user.id)
    )

@dp.callback_query(F.data.startswith("digit:"))
async def handle_digit(callback: CallbackQuery):
    val = callback.data.split(":")[1]
    st = user_state.setdefault(callback.from_user.id, {"from": "USD", "to": "RUB", "amount_str": ""})

    if val == "C":
        st["amount_str"] = ""
    elif val == ".":
        if "." not in st["amount_str"]:
            st["amount_str"] += "."
    else:
        st["amount_str"] += val
        if not st["amount_str"].startswith("0.") and len(st["amount_str"]) > 1:
            st["amount_str"] = st["amount_str"].lstrip("0") or "0"

    await callback.answer()
    await callback.message.edit_text(
        format_value(callback.from_user.id),
        reply_markup=main_calculator_kb(callback.from_user.id)
    )

# -----------------------------------------------------
# Запуск
# -----------------------------------------------------
if __name__ == "__main__":
    print("🔁 Запускаю polling...")
    asyncio.run(dp.start_polling(bot))
