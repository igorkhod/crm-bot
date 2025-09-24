# PROJECT_MAP.full.md — автогенерация
> Обновлено: Tue Sep 23 03:39:58 UTC 2025

## 📂 Структура файлов
### handlers
- `crm2/handlers/about.py`
- `crm2/handlers/admin/broadcast.py`
- `crm2/handlers/admin/chatgpt.py`
- `crm2/handlers/admin/logs.py`
- `crm2/handlers/admin/panel.py`
- `crm2/handlers/admin/schedule.py`
- `crm2/handlers/admin/users.py`
- `crm2/handlers/admin_db.py`
- `crm2/handlers/admin_db_doctor.py`
- `crm2/handlers/admin_users.py`
- `crm2/handlers/attendance.py`
- `crm2/handlers/auth.py`
- `crm2/handlers/consent.py`
- `crm2/handlers/help.py`
- `crm2/handlers/info.py`
- `crm2/handlers/profile.py`
- `crm2/handlers/registration.py`
- `crm2/handlers/start.py`
- `crm2/handlers/welcome.py`
### db
- `crm2/db/__init__.py`
- `crm2/db/attendance.py`
- `crm2/db/auto_migrate.py`
- `crm2/db/bootstrap.py`
- `crm2/db/content_loader.py`
- `crm2/db/core.py`
- `crm2/db/events.py`
- `crm2/db/migrate_admin.py`
- `crm2/db/schedule_loader.py`
- `crm2/db/schedule_repo.py`
- `crm2/db/sessions.py`
- `crm2/db/sqlite.py`
- `crm2/db/users.py`
- `crm2/db/users_repo.py`
### services
- `crm2/services/chatgpt_status.py`
- `crm2/services/content_loader.py`
- `crm2/services/schedule.py`
- `crm2/services/services.py`
- `crm2/services/users.py`
### keyboards
- `crm2/keyboards/__init__.py`
- `crm2/keyboards/_impl.py`
- `crm2/keyboards/admin_attendance.py`
- `crm2/keyboards/admin_schedule.py`
- `crm2/keyboards/admin_users.py`
- `crm2/keyboards/agents.py`
- `crm2/keyboards/info_menu.py`
- `crm2/keyboards/main_menu.py`
- `crm2/keyboards/profile.py`
- `crm2/keyboards/project.py`
- `crm2/keyboards/schedule.py`
- `crm2/keyboards/session_picker.py`

## ⚙️ Переменные окружения (.env.example)
- `TELEGRAM_TOKEN=ваш_токен_бота`
- `ADMIN_ID=ваш_telegram_id_цифрами  # например 448124106`
- `LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR`
- `TELEGRAM_TOKEN=82866_сокращено безопасностью`
- `WEATHER_API_KEY=55449_сокращено безопасностью`
- `ADMIN_ID=44812_сокращено безопасностью`
- `IGOR_KHOD_DEEPSEEK_API_KEY=sk-76422_сокращено безопасностью`
- `IGOR_OPENAI_API=sk-proj_сокращено безопасностью`
- `DEBUG_FULL_EXIT=1`
- `NOTIFY_STARTUP=1`
- `NOTIFY_SHUTDOWN=1`

## 🗄 Таблицы БД
(БД недоступна, используем DB_PATH=/var/data/crm.db)