import telebot
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random
from telebot import types

TOKEN = "8101400368:AAEOltM7ms9iXV4xXGALB1IQwzOxGEy5nAg"

JOKES = [
"1. **— Почему программисты путают Хэллоуин и Рождество?** — Потому что `31 OCT == 25 DEC`.",
"2. ** Программист на свидании:** — Ты мне нравишься… *if ты не против*.",
"3. **— Как называют программиста в лифте?** — *Elevator exception: Out of context*.",
"4. **— Почему программисты не любят природу?**  — Там *баги* — и нет *Ctrl+F*.",
"5. **— Сколько программистов нужно, чтобы вкрутить лампочку?** — Ни одного. Это *hardware problem*.",
"6. **— Почему код не работает?** — *Потому что ты его не компилировал… в своей голове.*",
"7. **— Как программист называет свою жену?** — *«Локальный хост»*.",
"8. **— Почему программист всегда мёрзнет?** — Потому что *окна* у него всегда открыты.",
"9. **— Что сказал *null*, встретив *undefined*?**  — *«Ты даже не ошибка!»*.",
"10. **— Почему программисты ненавидят кофе без кофеина?** — Потому что *decaf* — это *decarriage return*.",
"11. **— Какой напиток в баре закажет программист?** — *«Байт-колу»*.",
"12. **— Почему программист умер в душе?** — *Инструкция на шампуне: «Нанести, смыть, повторить»*.",
"13. **— Git commit -m Фикс** — *…но ничего не починил*.",
"14. **— Почему программисты не играют в прятки?** — *Потому что void main() { hide(); }* — их всё равно найдут.",
"15. **— Программист пишет завещание:** — *«Всё моё имущество — в main branch»*."
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот-шутник! \nНапиши /joke чтобы получить случайную шутку")

async def tell_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    random_joke = random.choice(JOKES)
    await update.message.reply_text(f"{random_joke}\n\n(/joke - ещё шутка)")

def maim():
    app = Application.builder().token(TOKEN).build()

    types.KeyboardButton(text="/joke")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("joke", tell_joke))

    app.run_polling()

if __name__ == '__main__':
    maim()