# === Автогенерированный заголовок: crm2/keyboards/project.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: project_menu_kb
# === Конец автозаголовка
# crm2/keyboards/project.py
from aiogram.utils.keyboard import InlineKeyboardBuilder

def project_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Режим проведения занятий", callback_data="info:mode")
    kb.button(text="Смыслы, заложенные в проекте", callback_data="info:meanings")
    kb.button(text="↩️ Главное меню", callback_data="info:mainmenu")
    kb.adjust(1)
    return kb.as_markup()

# def project_menu_kb() -> ReplyKeyboard↩️ Главное менюMarkup:
#     rows = [
#         [KeyboardButton(text="Как проводятся занятия")],
#         [KeyboardButton(text="↩️ Главное меню")],
#     ]
#     return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
