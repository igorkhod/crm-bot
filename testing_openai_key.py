import os
import openai
from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv('token.env')  # Убедитесь, что файл в той же папке
print("Токен OpenAI:", os.getenv('IGOR_OPENAI_API')[:5] + "...")  # Проверка загрузки


client = OpenAI(api_key=os.getenv('IGOR_OPENAI_API'))

try:
    print("Проверка ключа OpenAI...")
    models = client.models.list()
    print(f"✅ Ключ работает! Доступно моделей: {len(models.data)}")
except Exception as e:
    print(f"❌ Ошибка: {str(e)}")