# === Автогенерированный заголовок:"
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: _admin_menu_kb, admin_panel_kb, render_admin_panel, admin_entry_msg, admin_open_cb, admin_users_entry, admin_schedule_entry, admin_broadcast_entry, admin_logs_entry, admin_dbdoctor_entry, admin_dbdoctor_entry_text
# === Конец автозаголовка
# crm2/handlers/admin/panel.py
# 📄 crm2/handlers/admin/panel.py
# panel
# Назначение: обработчик и клавиатура админ-панели.
# Что делает:
# формирует inline-меню админки с кнопками: 👥 Пользователи, 🗓 Расписание, 📣 Рассылка, 🧾 Логи, 🩺 DB Doctor, 🤖 ChatGPT;
# рендерит админ-панель в сообщениях и callback-ответах;
# реализует заглушки для перехода в разделы (расписание, рассылка, логи);
# перенаправляет в отдельные модули для DB Doctor и ChatGPT.
# Расположение:
# crm2/
#  └── handlers/
#       └── admin/
#            └── panel.py
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

from crm2.keyboards import admin_panel_kb

# Если у тебя есть ограничитель доступа для админов — подключаем
try:
    from crm2.utils.guards import AdminOnly
except Exception:
    AdminOnly = None  # не критично, работаем и без middleware

router = Router(name="admin_panel")
if AdminOnly:
    router.message.middleware(AdminOnly())
    router.callback_query.middleware(AdminOnly())


# --- Клавиатура админ-панели ---------------------------------------------------

def _admin_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="👥 Пользователи", callback_data="adm:users"),
            InlineKeyboardButton(text="🗓 Расписание", callback_data="adm:schedule"),
        ],
        [
            InlineKeyboardButton(text="📋 Посещаемость", callback_data="adm:attendance"),
            InlineKeyboardButton(text="📚 Домашние задания", callback_data="adm:homework"),
        ],
        [
            InlineKeyboardButton(text="📣 Рассылка", callback_data="adm:broadcast"),
            InlineKeyboardButton(text="🧾 Логи", callback_data="adm:logs"),
        ],

        [
            InlineKeyboardButton(text="🩺 DB Doctor", callback_data="adm:dbdoctor"),
            InlineKeyboardButton(text="🤖 ChatGPT", callback_data="adm:chatgpt_status"),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=rows)


# алиас на случай импортов вида admin_panel_kb()
def admin_panel_kb() -> InlineKeyboardMarkup:
    return _admin_menu_kb()


# --- Единая функция рендера панели (и для message, и для callback) -------------
async def render_admin_panel(msg: Message):
    try:
        await msg.edit_text("Админ-панель:", reply_markup=_admin_menu_kb())
    except TelegramBadRequest:
        # если редактировать нельзя (другое сообщение/старое), отправим новое
        await msg.answer("Админ-панель:", reply_markup=_admin_menu_kb())


# --- Вход в админку по сообщению ----------------------------------------------
@router.message(F.text.in_({"⚙️ Админ", "Админ", "/admin"}))
async def admin_entry_msg(msg: Message):
    await render_admin_panel(msg)


# --- Вход/возврат по inline-колбэкам ------------------------------------------
@router.callback_query(F.data.in_({"adm:panel", "adm:open", "admin:back"}))
async def admin_open_cb(cb: CallbackQuery):
    await render_admin_panel(cb.message)
    await cb.answer()


# --- Новый раздел: Посещаемость ------------------------------------------------
@router.callback_query(F.data == "adm:attendance")
async def admin_attendance_entry(cb: CallbackQuery):
    # делегируем вывод меню в модуль admin_attendance
    from crm2.handlers import admin_attendance
    await admin_attendance.show_attendance_menu(cb.message)  # ожидает Message
    await cb.answer()

    # --- Новый раздел: Домашние задания -------------------------------------------


@router.callback_query(F.data == "adm:homework")
async def admin_homework_entry(cb: CallbackQuery):
    from crm2.handlers import admin_attendance
    await admin_attendance.show_homework_menu(cb.message)  # ожидает Message
    await cb.answer()


# --- Переход в раздел "Пользователи" ------------------------------------------
@router.callback_query(F.data == "adm:users")
async def admin_users_entry(cb: CallbackQuery):
    # показываем подменю с выбором групп пользователей
    from crm2.keyboards.admin_users import users_groups_kb
    await cb.message.edit_text("Выберите интересующую вас группу:", reply_markup=users_groups_kb())
    await cb.answer()


# --- Заглушки для остальных пунктов (можно заменить на реальные модули) -------
@router.callback_query(F.data == "adm:schedule")
async def admin_schedule_entry(cb: CallbackQuery):
    await cb.message.edit_text("🗓 Расписание → импорт XLSX и просмотр ближайших занятий.")
    await cb.answer()


@router.callback_query(F.data == "adm:broadcast")
async def admin_broadcast_entry(cb: CallbackQuery):
    await cb.message.edit_text("📣 Рассылка → запустите мастер-рассылки.")
    await cb.answer()


@router.callback_query(F.data == "adm:logs")
async def admin_logs_entry(cb: CallbackQuery):
    await cb.message.edit_text("🧾 Логи → сводка по рассылкам и служебные записи.")
    await cb.answer()


# --- Переход в раздел «DB Doctor» (inline-кнопка в админ-меню) ----------------
@router.callback_query(F.data == "adm:dbdoctor")
async def admin_dbdoctor_entry(cb: CallbackQuery):
    # выносим рендер меню в модуль доктора
    from crm2.handlers import admin_db_doctor
    await admin_db_doctor.show_menu(cb.message)  # show_menu ожидает Message
    await cb.answer()


# --- На всякий случай: если кнопка придёт текстом (reply-клавиатура) ----------
@router.message(F.text == "🩺 DB Doctor")
async def admin_dbdoctor_entry_text(message: Message):
    from crm2.handlers import admin_db_doctor
    await admin_db_doctor.show_menu(message)
