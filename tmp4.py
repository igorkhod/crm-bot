import os
from dotenv import load_dotenv
from telebot import TeleBot, types

# Загрузка .env
load_dotenv('token.env')  # Убедитесь, что файл лежит в той же папке, что и скрипт!

# Получаем токены
BOT_TOKEN = os.getenv('TOKEN')
DEEPSEEK_API = os.getenv('IGOR_KHOD_DEEPSEEK_API_KEY')
OPENAI_API = os.getenv('IGOR_OPENAI_API')

# Вывод первых 5 символов каждого ключа для проверки (удалите после отладки)
print("\n[DEBUG] Проверка загрузки токенов (первые 5 символов):")
print(f"BOT_TOKEN: {BOT_TOKEN[:5] + '...' if BOT_TOKEN else '❌ Не загружен!'}")
print(f"DEEPSEEK_API: {DEEPSEEK_API[:5] + '...' if DEEPSEEK_API else '❌ Не загружен!'}")
print(f"OPENAI_API: {OPENAI_API[:5] + '...' if OPENAI_API else '❌ Не загружен!'}\n")

# Проверяем, что все токены загружены
if None in [BOT_TOKEN, DEEPSEEK_API, OPENAI_API]:
    raise ValueError("Ошибка: Не все токены загружены из token.env!")

# Инициализация бота
bot = TeleBot(BOT_TOKEN)

# ... остальной код (как в предыдущих примерах) ...

if __name__ == '__main__':
    print("Бот запущен! Для остановки нажмите Ctrl+C")
    bot.polling()