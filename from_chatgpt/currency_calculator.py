import requests
from aiogram import F, types, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# 💱 Эмодзи и валюты
CURRENCIES = ["RUB", "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]
CURRENCY_EMOJIS = {
    "USD": "💵", "EUR": "💶", "RUB": "💴", "GBP": "💷",
    "JPY": "💴", "CHF": "💰", "AUD": "🦘", "CAD": "🍁", "NZD": "🐑"
}

user_state = {}

def emoji(cur: str) -> str:
    return CURRENCY_EMOJIS.get(cur, "")

def get_rate(base: str, symbol: str) -> float:
    url = f"https://open.er-api.com/v6/latest/{base}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        return data["rates"].get(symbol, 1)
    except Exception:
        return 1

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

def main_calculator_kb(user_id: int) -> InlineKeyboardMarkup:
    st = user_state.get(user_id, {"from": "USD", "to": "RUB"})
    buttons = []

    buttons.append([
        InlineKeyboardButton(text=f"{emoji(st['from'])} {st['from']}", callback_data="currency_calc:choose_from"),
        InlineKeyboardButton(text="⇄", callback_data="currency_calc:swap"),
        InlineKeyboardButton(text=f"{emoji(st['to'])} {st['to']}", callback_data="currency_calc:choose_to"),
    ])

    layout = [
        ["7", "8", "9"],
        ["4", "5", "6"],
        ["1", "2", "3"],
        ["0", ".", "C"]
    ]
    for row in layout:
        buttons.append([
            InlineKeyboardButton(text=x, callback_data=f"currency_calc:digit:{x}") for x in row
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 В меню", callback_data="currency_calc:exit")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def currency_keyboard(prefix: str):
    kb = InlineKeyboardBuilder()
    for cur in CURRENCIES:
        kb.button(text=f"{emoji(cur)} {cur}", callback_data=f"currency_calc:{prefix}:{cur}")
    kb.adjust(3)
    kb.row(InlineKeyboardButton(text="🔙 Назад", callback_data="currency_calc:back"))
    return kb.as_markup()

def register_currency_handlers(dp: Dispatcher, main_menu_callback):

    @dp.callback_query(F.data == "currency_calc:exit")
    async def exit_currency(callback: types.CallbackQuery):
        user_state.pop(callback.from_user.id, None)
        await callback.answer()
        await main_menu_callback(callback.message)

    @dp.callback_query(F.data == "currency_calc:choose_from")
    async def choose_from(callback: types.CallbackQuery):
        await callback.message.edit_text("Выберите исходную валюту:", reply_markup=currency_keyboard("from"))

    @dp.callback_query(F.data == "currency_calc:choose_to")
    async def choose_to(callback: types.CallbackQuery):
        await callback.message.edit_text("Выберите целевую валюту:", reply_markup=currency_keyboard("to"))

    @dp.callback_query(F.data == "currency_calc:back")
    async def back(callback: types.CallbackQuery):
        await callback.message.edit_text(
            format_value(callback.from_user.id),
            reply_markup=main_calculator_kb(callback.from_user.id)
        )

    @dp.callback_query(F.data == "currency_calc:swap")
    async def swap(callback: types.CallbackQuery):
        st = user_state.setdefault(callback.from_user.id, {"from": "USD", "to": "RUB", "amount_str": ""})
        st["from"], st["to"] = st["to"], st["from"]
        await callback.answer("🔄 Обмен выполнен")
        await callback.message.edit_text(
            format_value(callback.from_user.id),
            reply_markup=main_calculator_kb(callback.from_user.id)
        )

    @dp.callback_query(F.data.startswith("currency_calc:from:"))
    async def set_from(callback: types.CallbackQuery):
        cur = callback.data.split(":")[2]
        user_state.setdefault(callback.from_user.id, {})["from"] = cur
        await callback.message.edit_text(
            f"✅ Выбрана валюта {emoji(cur)} {cur}",
            reply_markup=main_calculator_kb(callback.from_user.id)
        )

    @dp.callback_query(F.data.startswith("currency_calc:to:"))
    async def set_to(callback: types.CallbackQuery):
        cur = callback.data.split(":")[2]
        user_state.setdefault(callback.from_user.id, {})["to"] = cur
        await callback.message.edit_text(
            f"✅ Выбрана валюта {emoji(cur)} {cur}",
            reply_markup=main_calculator_kb(callback.from_user.id)
        )

    @dp.callback_query(F.data.startswith("currency_calc:digit:"))
    async def digits(callback: types.CallbackQuery):
        val = callback.data.split(":")[2]
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
