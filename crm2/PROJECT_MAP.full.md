# PROJECT_MAP.full.md

---

# app.py — экспорт `bot`, `dp` и подключение роутеров

**Назначение:** точка инициализации aiogram, БД и маршрутов.

- `bot: aiogram.Bot` — создаётся на верхнем уровне модуля:
  ```python
  import os
  from aiogram import Bot, Dispatcher

  TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
  bot = Bot(token=TELEGRAM_TOKEN)
  dp = Dispatcher()
  ```
- Используется `EnvironmentFile=/opt/psytech-bot/app/token.env` (systemd), поэтому переменные окружения доступны процессу.
- Подключение роутеров:
  ```python
  from crm2.handlers import admin_attendance
  dp.include_router(admin_attendance.router)
  ```
- Экспортируемые объекты:
  - `bot` — нужен для отправки сообщений из хендлеров.
  - `dp` — главный диспетчер.

---

# handlers/admin_attendance.py — отметки и рассылка ДЗ

**Команды:**
- `/homework_send <session_id> <ссылка>` — отправляет ДЗ всем присутствовавшим на занятии.

**Зависимости:**
- Импорт бота из `app.py`:
  ```python
  from crm2.app import bot
  ```
- Сервис работы с БД:
  ```python
  from crm2.services import attendance
  ```

**Схема работы:**
1. Парсит `session_id` и ссылку.
2. Через `attendance.get_present_users(session_id)` получает список `user_id` со статусом `'present'`.
3. Рассылает сообщение с ссылкой каждому пользователю.
4. Отчитывается админу по количеству отправок/ошибок.

**Фрагмент:**
```python
from aiogram import Router, F
from aiogram.types import Message
from crm2.services import attendance
from crm2.app import bot

router = Router()

@router.message(F.text.startswith("/homework_send"))
async def send_homework(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("⚠️ Используй: /homework_send <session_id> <ссылка>")
        return
    session_id = int(parts[1]); link = parts[2]

    user_ids = await attendance.get_present_users(session_id)
    sent = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, f"📚 Домашнее задание по занятию {session_id}:\n{link}")
            sent += 1
        except Exception as e:
            await message.answer(f"❌ Не удалось отправить {uid}: {e}")

    await message.answer(f"✅ ДЗ отправлено {sent} курсантам")
```

---

# services/attendance.py — интерфейс к таблице `attendance`

**Контракт таблицы `attendance`:**
- `id INTEGER PRIMARY KEY`
- `user_id INTEGER NOT NULL`
- `session_id INTEGER NOT NULL`
- `status TEXT NOT NULL CHECK(status IN ('present','absent','late'))`
- `noted_at TEXT DEFAULT CURRENT_TIMESTAMP`
- `noted_by INTEGER`
- Уникальный индекс: `UNIQUE(user_id, session_id)`.

**Публичные функции:**
```python
from crm2.db import db

async def mark_attendance(user_id: int, session_id: int, status: str, noted_by: int):
    '''
    UPSERT записи посещаемости.
    status ∈ {'present','absent'} (опционально 'late' в будущем)
    '''
    sql = """
    INSERT INTO attendance (user_id, session_id, status, noted_by)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id, session_id)
    DO UPDATE SET status=excluded.status,
                  noted_at=CURRENT_TIMESTAMP,
                  noted_by=excluded.noted_by
    """
    await db.execute(sql, (user_id, session_id, status, noted_by))

async def get_present_users(session_id: int) -> list[int]:
    '''
    Список user_id, у кого status='present' на заданной сессии.
    '''
    rows = await db.fetch_all(
        "SELECT user_id FROM attendance WHERE session_id=? AND status='present'",
        (session_id,)
    )
    return [row[0] for row in rows]
```

**Примечание:** если решим перейти на числовые статусы 0/1, потребуется миграция CHECK и маппинг.
