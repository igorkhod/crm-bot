from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from crm2.utils.guards import AdminOnly

router = Router()
router.message.middleware(AdminOnly())
router.callback_query.middleware(AdminOnly())

def admin_menu_kb():
    rows = [
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="adm:users"),
         InlineKeyboardButton(text="🗓 Расписание", callback_data="adm:schedule")],
        [InlineKeyboardButton(text="📣 Рассылка", callback_data="adm:broadcast"),
         InlineKeyboardButton(text="🧾 Логи", callback_data="adm:logs")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# --- ВХОД В АДМИНКУ ПО СООБЩЕНИЮ (reply-кнопка) ---
@router.message(F.text.in_({"⚙️ Админ", "🛠 Панель администратора", "/admin", "Админ"}))
async def admin_entry_msg(msg: Message):
    await msg.answer("Админ-панель:", reply_markup=admin_menu_kb())


# --- (опционально) ВХОД ПО INLINE-КНОПКЕ ---
@router.callback_query(F.data.in_({"adm:panel", "adm:open"}))
async def admin_entry_cb(cb: CallbackQuery):
    await cb.message.answer("Админ-панель:", reply_markup=admin_menu_kb())
    await cb.answer()


@router.message(F.text.in_({"⚙️ Админ", "/admin", "Админ"}))
async def admin_entry(msg: Message):
    await msg.answer("Админ-панель:", reply_markup=admin_menu_kb())

@router.callback_query(F.data == "adm:users")
async def admin_users_entry(cb: CallbackQuery):
    from crm2.keyboards.admin_users import users_groups_kb
    await cb.message.answer("Выберите интересующую вас группу:", reply_markup=users_groups_kb())
    # await cb.message.answer("👥 Пользователи → скоро тут будут списки, поиск и смена ролей.")
    await cb.answer()

@router.callback_query(F.data == "adm:schedule")
async def admin_schedule_entry(cb: CallbackQuery):
    await cb.message.answer("🗓 Расписание → импорт XLSX и просмотр ближайших занятий.")
    await cb.answer()

@router.callback_query(F.data == "adm:broadcast")
async def admin_broadcast_entry(cb: CallbackQuery):
    # реальный мастер-рассылки подключается отдельным модулем (handlers/admin/broadcast.py)
    await cb.message.answer("📣 Рассылка → запустите мастер-рассылки.")
    await cb.answer()

@router.callback_query(F.data == "adm:logs")
async def admin_logs_entry(cb: CallbackQuery):
    await cb.message.answer("🧾 Логи → сводка по рассылкам и служебные записи.")
    await cb.answer()