import os
import requests
from dotenv import load_dotenv

# Загрузка ключа из token.env
load_dotenv("token.env")
API_KEY = os.getenv("IGOR_KHOD_API_KEY")  # Убедитесь, что имя переменной совпадает!


def ask_deepseek(prompt: str) -> str:
    """Отправляет запрос к DeepSeek API и возвращает ответ."""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",  # Уточните модель в документации
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7  # Контроль "креативности" (от 0 до 1)
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",  # Уточните URL!
            headers=headers,
            json=data,
            timeout=10  # Таймаут запроса (секунды)
        )
        response_data = response.json()

        # Дебаг: выводим полный ответ API
        print("Ответ API:", response_data)

        if "choices" in response_data:
            return response_data["choices"][0]["message"]["content"]
        elif "error" in response_data:
            return f"Ошибка API: {response_data['error']['message']}"
        else:
            return "Неизвестный формат ответа"

    except requests.exceptions.RequestException as e:
        return f"Ошибка сети: {str(e)}"
    except Exception as e:
        return f"Неожиданная ошибка: {str(e)}"


# Тест
if __name__ == "__main__":
    question = "Привет! Ответь кратко: как работает твой API?"
    answer = ask_deepseek(question)
    print("Ответ ИИ:", answer)