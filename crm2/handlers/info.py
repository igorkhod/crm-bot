#
# === Файл: crm2/handlers/info.py
# Аннотация: модуль CRM, хендлеры и маршрутизация событий Telegram, Telegram-бот на aiogram 3.x. Внутри функции: _get, _code, _fmt_date, _build_details_kb, show_schedule....
# Добавлено автоматически 2025-08-21 05:43:17

# crm2/handlers/info.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Message, CallbackQuery

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


@router.message(F.text == "🤖 ИИ-агенты")
async def show_agents(message: Message):
    await message.answer("Выберите ИИ-агента:", reply_markup=agents_menu_kb())


@router.message(F.text == "🧘 Волевая медитация (необходима VPN)")
async def open_meditation(message: Message):
    await message.answer(
        "Открыть: [Волевая медитация](https://chatgpt.com/g/g-6871e6ae78c481918109e8813e51bc84-volevaia-meditatsiia)",
        disable_web_page_preview=True,
    )


@router.message(F.text == "⚖️ Психотехнологии гармонии (необходима VPN)")
async def open_harmony(message: Message):
    await message.answer(
        "Открыть: [Психотехнологии гармонии](https://chatgpt.com/g/g-687493b5969c8191975066fd9970bd24-psikhotekhnologii-garmonii)",
        disable_web_page_preview=True,
    )

@router.message(F.text == "Инструкция по подключению ChatGPT-АГЕНТОВ")
async def open_agents_instruction(message: Message):
    await message.answer(
        "📖 *Инструкция по подключению ChatGPT-АГЕНТОВ*\n"
        "1️⃣ Убедитесь, что у вас включён VPN (ChatGPT может быть недоступен без него).\n"
        "2️⃣ Нажмите на кнопку нужного агента в меню «ИИ-агенты».\n"
        "3️⃣ В открывшейся странице выберите вход через Google (*Continue with Google*).\n"
        "4️⃣ Выберите свой Google-аккаунт и подтвердите вход.\n"
        "5️⃣ После входа откроется страница агента. Нажмите ⭐️ *Add to favorites* или «Добавить в избранное», "
        "чтобы сохранить агента у себя в ChatGPT.\n"
        "💡 *Важно:* пользование GPT-агентами не требует оплаты — достаточно бесплатного аккаунта ChatGPT.\n"
        "Теперь агент всегда будет доступен в вашем списке чатов в ChatGPT.\n"
        "ℹ️ Подсказка: если агент не открывается — проверьте VPN или попробуйте другой браузер.\n"
        "Если у вас нет друзей за границей, можно поступить традиционным путём,\n"
        "открываете поиск в яндексе или гугле, вводите запрос: Регистрация в ChatGPT.\n"
        "📝 например: https://yandex.ru/video/preview/15095507383715000533\n"
        "📝 например: https://yandex.ru/video/preview/5822067052173058585\n"
        "регистрация через зарубежного знакомого на ChatGPT\n"
        "вкратце: нужно, что бы у вас был друг,\n"
        "например - в колумбии, или как у меня\n"
        "дочь, в аргентине, которые\n"
        "зарегистрирует дополнительный google\n"
        "аккаунт, особенность в том, что в\n"
        "ChatGPT заблокированы российские адреса\n"
        "e-mail и российские телефоны, по которым\n"
        "запрашивается подтверждение регистрации.\n"
        "Поэтому\n"
        "1.	Ваш знакомый регистрирует для\n"
        "вас почтовый ящик на gmail.com.\n"
        "2.	Подтверждает почтовый ящик через\n"
        "свой телефон.\n"
        "3.	Регистрируется на chatgpt.com\n"
        "через этот google-аккаунт. и даёт вам\n"
        "доступ к этому гугл-аккаунту, сообщая\n"
        "адреc на gmail.com и пароль к почтовому\n"
        "ящику, что бы вы могли с этим аккаунтом\n"
        "входить в chatgpt.\n"
        "4.	Но для первого входа в google-\n"
        "аккаунт вам потребуется срочный и\n"
        "непосредственный контакт с другом по\n"
        "телеграму или вацапу, поскольку вы\n"
        "будете входить в аккаунт со своего\n"
        "устройства, а это отслеживается.\n"
        "Потребуется подтверждение, что это\n"
        "входит, типа ваш друг, но с вашего\n"
        "устройства. Вашему другу придёт СМС на\n"
        "подтверждение входа в google-аккаунт в\n"
        "виде числа и это число вам нужно будет\n"
        "ввести по запросу, что его аккаунтом\n"
        "хочет воспользоваться другой человек.\n"
        "это делается один единственный раз.\n"
        "Иногда google требует подтверждение ещё\n"
        "один раз. Ещё подтверждение может\n"
        "потребоваться при вашей регистрации на\n"
        "chatgpt.com, никаких платежей вам делать\n"
        "не нужно, если вы не захотите доп услуг,\n"
        "после регистрации вам станут доступны\n"
        "все ИИ-агенты бесплатно.\n"

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


# --- О проекте ---
from crm2.keyboards.project import project_menu_kb
from crm2.keyboards import role_kb, guest_start_kb
import sqlite3
from crm2.db.sqlite import DB_PATH


@router.message(F.text == "📖 О проекте")
async def show_project_menu(message: Message):
    await message.answer("ℹ️ Информация о проекте:", reply_markup=project_menu_kb())


@router.message(F.text == "Как проводятся занятия")
async def how_sessions_go(message: Message):
    text = (
        "🧘‍♂️ *Как проходят занятия Psytech*\n"
        "Занятия строятся в формате психотехнологических практик.\n"
        "🔹 Теория — краткие вводные идеи, чтобы направить внимание.\n"
        "🔹 Практика — упражнения на концентрацию, деконцентрацию, "
        "управление состояниями и работу с волей.\n"
        "🔹 Рефлексия — обсуждение опыта и интеграция его в жизнь.\n"
        "Мы соединяем древние традиции и современные методы, чтобы "
        "человек обрел ясность, устойчивость и гармонию."
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "↩️ Главное меню")
async def back_to_main_from_project(message: Message):
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT role FROM users WHERE telegram_id = ? LIMIT 1", (message.from_user.id,)).fetchone()
        role = row["role"] if row else "curious"

    if role in (None, "", "curious"):
        await message.answer("Главное меню:", reply_markup=guest_start_kb())
    else:
        await message.answer(f"Главное меню (ваша роль: {role})", reply_markup=role_kb(role))
