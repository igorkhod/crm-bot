from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from crm2.utils.guards import AdminOnly

router = Router()
router.message.middleware(AdminOnly())
router.callback_query.middleware(AdminOnly())

def admin_kb():
    rows = [
      [InlineKeyboardButton(text="📤 Рассылка", callback_data="adm:broadcast"),
       InlineKeyboardButton(text="📦 Материалы", callback_data="adm:materials")],
      [InlineKeyboardButton(text="📝 Домашние задания", callback_data="adm:assign")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.message(F.text.in_({"⚙️ Админ", "/admin", "Админ"}))
async def admin_entry(msg: Message):
    await msg.answer("Админ-панель:", reply_markup=admin_kb())
