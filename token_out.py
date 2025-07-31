import os
from dotenv import load_dotenv
from telegram.ext import Application

# Загружаем токен (теперь ищем переменную TOKEN вместо TELEGRAM_BOT_TOKEN)
load_dotenv("token.env")
TOKEN = os.getenv("TOKEN")  # Обратите внимание на имя переменной

if not TOKEN:
    raise ValueError("❌ Токен не найден! Проверьте файл token.env")
print(f"✅ Токен загружен (первые 5 символов): {TOKEN[:5]}...")

app = Application.builder().token(TOKEN).build()
print("🟢 Бот успешно запущен!")
app.run_polling()