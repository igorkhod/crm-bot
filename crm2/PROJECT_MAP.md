# PROJECT_MAP

Обновлено: 2025-09-25T09:52:10.291427Z

## Назначение ключевых модулей
- **app.py** — точка входа: загрузка .env, инициализация `Bot/Dispatcher`, включение роутеров.
- **panel.py** — хендлеры разделов админ-панели (кнопки: Посещаемость, Домашние задания, и т.д.).
- **admin_attendance.py** — логика отметки посещаемости (`/attendance_*`).
- **admin_homework.py** — рассылка ДЗ по `session_id` только «present» пользователям (`/homework_*`).
- **admin_users.py** — просмотр/пагинация пользователей.
- **admin_db.py** — диагностика и утилиты БД (только админам).
- **schedule.py** — утилиты/форматирование расписания (клавиатуры, даты).
- **crm2/handlers/info.py** - (хендлеры расписания, проекта и меню)
- **crm2/services/users.py** (функции работы с пользователями,


## Бизнес-поток
1. Админ → «⚙️ Админ» → «🧾 Посещаемость». Отмечает *present* по `session_id`.
2. Админ → «📚 Домашние задания» → `/homework_send <session_id> <url>`.
3. `/homework_status <session_id>` — проверка, `/homework_reset <session_id>` — сброс меток отправок.

## Примечания по коду
- Aiogram 3.7+: `Bot(default=DefaultBotProperties(parse_mode="HTML"))`.
- Хендлеры подключаются безопасно; падение одного модуля не блокирует запуск — ошибки логируются.
- Разделение конфигов: `.env.local` (локально) и `.env.prod` (VPS).

## Изменения в этом архиве
{
  "panel.py": "+ router hint",
  "admin_attendance.py": "+ router hint",
  "admin_homework.py": "+ router hint",
  "admin_db.py": "+ router hint"
}

