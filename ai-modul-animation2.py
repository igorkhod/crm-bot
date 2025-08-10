import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update, Message, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Конфигурация
load_dotenv('token.env')
TOKEN = os.getenv('TOKEN')
API_KEY = os.getenv('IGOR_KHOD_API_KEY')


class AIBot:
    def __init__(self):
        self.API_URL = "https://api.deepseek.com/v1/chat/completions"
        self.API_TIMEOUT = 10
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 1.5

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Инициализация бота с кнопкой"""
        button = KeyboardButton("🔄 Спросить ИИ")
        reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
        await update.message.reply_text(
            "🤖 Готов к вопросам! Нажмите кнопку ниже:",
            reply_markup=reply_markup
        )

    async def show_animation(self, update: Update) -> Message:
        """Визуальная анимация загрузки"""
        phases = [
            "🔍 Анализирую запрос",
            "🔍 Анализирую запрос.",
            "🔍 Анализирую запрос..",
            "🧠 Формирую ответ",
            "🧠 Формирую ответ.",
            "🧠 Формирую ответ.."
        ]
        msg = await update.message.reply_text(phases[0])

        for i in range(16):  # 8 секунд анимации
            await asyncio.sleep(0.5)
            try:
                await msg.edit_text(phases[i % len(phases)])
            except:
                break
        return msg

    async def query_ai(self, prompt: str) -> str:
        """Устойчивый запрос к API с повторами"""
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=self.API_TIMEOUT
                )
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']

            except requests.exceptions.Timeout:
                if attempt == self.MAX_RETRIES - 1:
                    raise Exception("Сервер не отвежает. Попробуйте позже ⏳")
                await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))

            except Exception as e:
                raise Exception(f"Ошибка API: {str(e)}")

    async def handle_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик вопросов"""
        if update.message.text == "🔄 Спросить ИИ":
            await update.message.reply_text("📝 Введите ваш вопрос:", reply_markup=None)
            context.user_data['awaiting_question'] = True
            return

        if not context.user_data.get('awaiting_question'):
            button = KeyboardButton("🔄 Спросить ИИ")
            reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
            await update.message.reply_text("Нажмите кнопку для вопроса:", reply_markup=reply_markup)
            return

        question = update.message.text
        processing_msg = None

        try:
            # Запуск анимации
            processing_msg = await self.show_animation(update)

            # Запрос к API
            answer = await self.query_ai(question)

            # Успешный ответ
            await processing_msg.delete()
            chunks = [answer[i:i + 4000] for i in range(0, len(answer), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)

        except Exception as e:
            error_msg = str(e)
            if processing_msg:
                await processing_msg.edit_text(error_msg)
            else:
                await update.message.reply_text(error_msg)

        finally:
            # Восстановление интерфейса
            button = KeyboardButton("🔄 Спросить ИИ")
            reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
            final_msg = "✅ Готов к новым вопросам!" if not processing_msg else ""
            await update.message.reply_text(final_msg, reply_markup=reply_markup)
            context.user_data['awaiting_question'] = False


def main():
    bot = AIBot()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_request))

    print("🟢 Бот запущен. Отправьте /start в Telegram.")
    app.run_polling()


if __name__ == "__main__":
    main()