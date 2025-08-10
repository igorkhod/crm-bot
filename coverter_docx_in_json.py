import json
from docx import Document
from pathlib import Path


def convert_docx_to_json(docx_path, json_path):
    """Конвертирует цитаты из DOCX в JSON (только текст)"""
    try:
        doc = Document(docx_path)
        quotes = []

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                # Если есть разделитель, берем только часть до него
                if "—" in text:
                    quote_text = text.split("—", 1)[0]
                elif "–" in text:
                    quote_text = text.split("–", 1)[0]
                else:
                    quote_text = text

                quotes.append({"text": quote_text.strip()})

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

        print(f"✅ Успешно конвертировано {len(quotes)} цитат")
        print(f"📄 Результат сохранен в {json_path}")

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")


# Пути к файлам
docx_file = Path("цитаты.docx")
json_file = Path("quotes.json")

if __name__ == "__main__":
    if docx_file.exists():
        convert_docx_to_json(docx_file, json_file)

        # Покажем первые 3 цитаты для проверки
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                sample = json.load(f)[:3]
            print("\nПример цитат:")
            for i, quote in enumerate(sample, 1):
                print(f"{i}. {quote['text']}")
        except:
            pass
    else:
        print(f"❌ Файл {docx_file} не найден!")