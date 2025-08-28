#
# === Файл: crm2/handlers/info.py
# Аннотация: модуль CRM, хендлеры и маршрутизация событий Telegram, Telegram-бот на aiogram 3.x. Внутри функции: _get, _code, _fmt_date, _build_details_kb, show_schedule....
# Добавлено автоматически 2025-08-21 05:43:17

# crm2/handlers/info.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from crm2.keyboards import role_kb
from crm2.services.schedule import upcoming  # элементы имеют поля start/end и, при наличии, topic_code/title/annotation

router = Router(name="info")


def _get(obj, key):
    """Достаёт поле и у объекта, и у dict."""
    try:
        return getattr(obj, key)
    except AttributeError:
        pass
    if isinstance(obj, dict):
        return obj.get(key)
    return None


def _code(it) -> str:
    """Берём индекс занятия по любому из возможных имён поля."""
    for k in ("topic_code", "code", "topic", "index"):
        v = _get(it, k)
        if v:
            return str(v)
    return ""


def _fmt_date(d) -> str:
    return d.strftime("%d.%m.%Y")


def _build_details_kb(items) -> InlineKeyboardMarkup:
    """Кнопки-строки: ДАТЫ + индекс курса."""
    rows = []
    for it in items:
        start = _get(it, "start")
        end = _get(it, "end") or start
        if not start:
            continue
        code = _code(it)
        text = f"{_fmt_date(start)} — {_fmt_date(end)}" + (f" • {code}" if code else "")
        cb = f"sess:{start.strftime('%Y%m%d')}"
        rows.append([InlineKeyboardButton(text=text, callback_data=cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text == "📅 Расписание")
async def show_schedule(message: Message):
    """Список занятий: даты + индекс в скобках; кнопки — даты + индекс."""
    items = upcoming(message.from_user.id, limit=100)
    if not items:
        await message.answer("Расписание занятий:\n• ближайших занятий пока нет.", reply_markup=role_kb("user"))
        return

    lines = ["Расписание занятий:"]
    for it in items:
        start = _get(it, "start")
        end = _get(it, "end") or start
        code = _code(it)
        code_txt = f" ({code})" if code else ""
        lines.append(f"• {_fmt_date(start)} — {_fmt_date(end)}{code_txt}")

    await message.answer("\n".join(lines), reply_markup=_build_details_kb(items))


@router.callback_query(F.data.startswith("sess:"))
async def session_details(cb: CallbackQuery):
    """Карточка занятия: даты, код, тема и аннотация."""
    start_key = cb.data.split(":", 1)[1]  # YYYYMMDD
    items = upcoming(cb.from_user.id, limit=200)

    target = None
    for it in items:
        s = _get(it, "start")
        if s and s.strftime("%Y%m%d") == start_key:
            target = it
            break

    if not target:
        await cb.answer("Не удалось найти запись :(", show_alert=True)
        return

    start = _get(target, "start")
    end = _get(target, "end") or start
    code = _code(target)
    title = _get(target, "title")
    ann = _get(target, "annotation")

    text = f"🗓 {_fmt_date(start)} — {_fmt_date(end)}"
    if code:
        text += f"\nКод: {code}"
    if title:
        text += f"\nТема: {title}"
    if ann:
        ann = ann if len(ann) <= 3600 else ann[:3600] + "…"
        text += "\nАннотация:\n" + ann

    await cb.message.answer(text, reply_markup=role_kb("user"))
    await cb.answer()

# ** *a / crm2 / handlers / info.py
# --- ИИ-агенты ---
from crm2.keyboards.agents import agents_menu_kb

@ router.message(F.text == "🤖 ИИ-агенты требуется VPN")
async def show_agents(message: Message):
    await message.answer("Выберите ИИ-агента:", reply_markup=agents_menu_kb())


@ router.message(F.text == "🧘 Волевая медитация требуется VPN")
async def open_meditation(message: Message):
    await message.answer(
        "Открыть: [Волевая медитация](https://chatgpt.com/g/g-6871e6ae78c481918109e8813e51bc84-volevaia-meditatsiia)",
        disable_web_page_preview = True,
    )


@ router.message(F.text == "⚖️ Психотехнологии гармонии требуется VPN")
async def open_harmony(message: Message):
    await message.answer(
        "Открыть: [Психотехнологии гармонии](https://chatgpt.com/g/g-687493b5969c8191975066fd9970bd24-psikhotekhnologii-garmonii)",
        disable_web_page_preview = True,
    )


@router.message(F.text == "↩️ Главное меню")
async def back_to_main(message: Message):
    from crm2.keyboards import role_kb, guest_start_kb
    from crm2.db.sqlite import DB_PATH
    import sqlite3

    # Определяем роль из базы
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.execute("SELECT role FROM users WHERE telegram_id=?", (message.from_user.id,))
        row = cur.fetchone()
        role = row["role"] if row else "curious"

    if role in (None, "", "curious"):
        await message.answer("Главное меню:", reply_markup=guest_start_kb())
    else:
        await message.answer(f"Главное меню (ваша роль: {role})", reply_markup=role_kb(role))
