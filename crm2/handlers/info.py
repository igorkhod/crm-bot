# crm2/handlers/info.py
# Назначение: Многофункциональный модуль информации - расписание, ИИ-агенты, проект и общая навигация
# Функции:
# - _get - Универсальный доступ к полям объектов и словарей
# - _code - Извлечение кода занятия из различных полей
# - _fmt_date - Форматирование даты в читаемый вид
# - _build_details_kb - Построение клавиатуры деталей сессий
# - _show_schedule_list - Вспомогательный показ списка расписания
# Обработчики:
# - show_schedule_menu - Главное меню расписания
# - session_details - Детальная информация о выбранной сессии
# - show_agents - Меню ИИ-агентов
# - open_meditation - Ссылка на агента "Волевая медитация"
# - open_harmony - Ссылка на агента "Психотехнологии гармонии"
# - open_agents_instruction - Подробная инструкция по подключению ChatGPT
# - show_project_menu - Меню информации о проекте
# - how_sessions_go - Устаревший обработчик (редирект на проект)
# - back_to_main_from_project - Возврат в главное меню с учетом роли
# - on_events - Обработчик мероприятий (заглушка)
# - on_all - Показ общего расписания всех событий
# - on_cohort - Навигация по расписанию когорт с пагинацией дат
# - on_info_mode - Показ информации о режиме проекта
# - on_info_meanings - Ссылка на смыслы проекта (внешний ресурс)
# - on_info_mainmenu - Возврат в меню информации о проекте
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Message, CallbackQuery

from crm2.services.schedule import upcoming  # элементы имеют поля start/end и, при наличии, topic_code/title/annotation
from crm2.keyboards import schedule_root_kb, role_kb, schedule_dates_kb
from crm2.services import schedule as sch
from crm2.keyboards.project import project_menu_kb
from crm2.keyboards import role_kb, guest_start_kb
import sqlite3
from crm2.db.sqlite import DB_PATH
from aiogram.exceptions import TelegramBadRequest
from crm2.keyboards.project import project_menu_kb
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os


router = Router(name="info")

@router.message(F.text == "📅 Расписание")
async def show_schedule_menu(message: Message):
    await message.answer("Выберите, что показать:", reply_markup=schedule_root_kb())


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


async def _show_schedule_list(message: Message):
    """Вспомогательная печать списка (используется при необходимости)."""
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
        "📝 например: https://yandex.ru/video/preview/5822067052173058585\n\n"
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


# --- О проекте ---
from crm2.keyboards.project import project_menu_kb
from crm2.keyboards import role_kb, guest_start_kb
import sqlite3
from crm2.db.sqlite import DB_PATH


@router.message(F.text.in_({"ℹ️ Информация о проекте", "📖 О проекте"}))
async def show_project_menu(message: Message):
    # Показываем подменю всем ролям (guest/user/admin)
    await message.answer("ℹ️ Информация о проекте:", reply_markup=project_menu_kb())


@router.message(F.text == "Как проводятся занятия")
async def show_project_menu_legacy(message: Message):
    # Роль можно использовать для будущей логики, но подменю показываем всем
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT role FROM users WHERE telegram_id = ? LIMIT 1",
            (message.from_user.id,)
        ).fetchone()
        role = (row["role"] if row else None) or "guest"

    await message.answer("ℹ️ Информация о проекте:", reply_markup=project_menu_kb())

@router.message(F.text == "↩️ Главное меню")
async def back_to_main_from_project(message: Message):
    from aiogram.types import ReplyKeyboardRemove
    import sqlite3
    from crm2.db.sqlite import DB_PATH
    from crm2.keyboards import role_kb, guest_start_kb

    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT role FROM users WHERE telegram_id = ? LIMIT 1",
            (message.from_user.id,)
        ).fetchone()
        role = (row["role"] if row else None) or "guest"

    # Гость не может «выйти в главное меню» изнутри раздела — сообщаем и убираем клавиатуру
    if role == "guest":
        await message.answer(
            "Для гостя доступна только информация «О проекте». "
            "Войдите, чтобы видеть главное меню.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # user/admin — как раньше
    await message.answer(f"Главное меню (ваша роль: {role})", reply_markup=role_kb(role))



from crm2.services import schedule as sch

@router.callback_query(F.data == "sch:events")
async def on_events(cb: CallbackQuery):
    await cb.answer()
    await cb.message.answer("Мероприятия пока не запланированы.")

@router.callback_query(F.data == "sch:all")
async def on_all(cb: CallbackQuery):
    await cb.answer()
    items = sch.list_all(limit=50)
    if not items:
        await cb.message.answer("Расписание всех событий:\n• пока нет будущих дат.")
        return
    lines = [f"• {s.start:%d.%m.%Y} — {s.end:%d.%m.%Y} ({s.code or s.title})" for s in items]
    await cb.message.answer("Расписание всех событий:\n" + "\n".join(lines))

@router.callback_query(F.data.startswith("sch:cohort:"))
async def on_cohort(cb: CallbackQuery):
    parts = cb.data.split(":")
    # форматы: "sch:cohort:2"  или  "sch:cohort:2:2025-09-13"
    if len(parts) == 3:
        # Показать даты для потока
        cohort_id = int(parts[2])
        items = sch.list_for_cohort(cohort_id, limit=5)
        if not items:
            await cb.message.answer(f"Расписание потока {cohort_id}:\n• пока нет будущих дат.")
            await cb.answer()
            return
        await cb.message.answer(f"Поток {cohort_id}: выберите дату:", reply_markup=schedule_dates_kb(cohort_id, items))
        await cb.answer()
        return

    if len(parts) == 4:
        cohort_id = int(parts[2]);
        date_iso = parts[3]
        # 1) поднимаем меню (шлём новый месседж с меню)
        await cb.message.answer("Выберите, что показать:", reply_markup=schedule_root_kb())
        # 2) деталь занятия
        s = sch.detail_for_cohort_date(cohort_id, date_iso)
        if not s:
            await cb.message.answer("Запись не найдена или нет описания.")
            await cb.answer()
            return
        span = s.start.strftime("%d.%m.%Y") if s.end == s.start else f"{s.start:%d.%m.%Y} — {s.end:%d.%m.%Y}"
        title = s.title or s.code or "Без названия"
        body = f"🗓 {span}\nТема: {title}\n\n{s.annotation}".strip()
        await cb.message.answer(body)
        await cb.answer()


from crm2.services.content_loader import load_html

@router.callback_query(F.data == "info:mode")
async def on_info_mode(cb: CallbackQuery):
    await cb.message.edit_text(load_html("mode"), parse_mode="HTML", disable_web_page_preview=True)
    await cb.answer()


from aiogram.utils.keyboard import InlineKeyboardBuilder
import os

@router.callback_query(F.data == "info:meanings")
async def on_info_meanings(cb: CallbackQuery):
    # 1) Можно указать свой URL через переменную окружения INFO_MEANINGS_URL
    url = os.getenv(
        "INFO_MEANINGS_URL",
        # 2) По умолчанию — страница файла в GitHub-репозитории
        "https://github.com/igorkhod/crm/blob/main/crm2/content/info/meanings.md"
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Открыть в браузере", url=url)
    kb.button(text="↩️ Главное меню", callback_data="info:mainmenu")
    kb.adjust(1, 1)

    await cb.message.edit_text(
        "📖 Смыслы проекта открываются во внешнем браузере:",
        reply_markup=kb.as_markup(),
        disable_web_page_preview=False
    )
    await cb.answer()



@router.callback_query(F.data == "info:mainmenu")
async def on_info_mainmenu(cb: CallbackQuery):
    try:
        await cb.message.edit_text(
            "ℹ️ Информация о проекте:",
            reply_markup=project_menu_kb()
        )
    except TelegramBadRequest as e:
        # если Telegram ругается "message is not modified"
        if "message is not modified" in str(e):
            try:
                # меняем только клавиатуру
                await cb.message.edit_reply_markup(reply_markup=project_menu_kb())
            except TelegramBadRequest:
                # крайний случай — отправим новое сообщение
                await cb.message.answer(
                    "ℹ️ Информация о проекте:",
                    reply_markup=project_menu_kb()
                )
        else:
            raise
    await cb.answer()