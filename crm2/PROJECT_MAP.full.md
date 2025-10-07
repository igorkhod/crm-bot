# PROJECT_MAP.full.md — автогенерация
> Обновлено: Tue Oct  7 05:33:14 UTC 2025

## 📂 Структура файлов
### handlers
- `crm2/handlers/__init__.py`
- `crm2/handlers/about.py`
- `crm2/handlers/admin/__init__.py`
- `crm2/handlers/admin/admin_homework.py`
- `crm2/handlers/admin/broadcast.py`
- `crm2/handlers/admin/chatgpt.py`
- `crm2/handlers/admin/logs.py`
- `crm2/handlers/admin/panel.py`
- `crm2/handlers/admin/schedule.py`
- `crm2/handlers/admin/stream_fix.py`
- `crm2/handlers/admin/users.py`
- `crm2/handlers/admin_attendance.py`
- `crm2/handlers/admin_db.py`
- `crm2/handlers/admin_db_doctor.py`
- `crm2/handlers/admin_homework.py`
- `crm2/handlers/admin_users.py`
- `crm2/handlers/attendance.py`
- `crm2/handlers/auth.py`
- `crm2/handlers/consent.py`
- `crm2/handlers/help.py`
- `crm2/handlers/info.py`
- `crm2/handlers/profile.py`
- `crm2/handlers/registration.py`
- `crm2/handlers/start.py`
- `crm2/handlers/stream_selfset.py`
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
- `crm2/services/attendance.py`
- `crm2/services/attendance2.py`
- `crm2/services/chatgpt_status.py`
- `crm2/services/content_loader.py`
- `crm2/services/participants.py`
- `crm2/services/schedule.py`
- `crm2/services/services.py`
- `crm2/services/users.py`
### keyboards
- `crm2/keyboards/__init__.py`
- `crm2/keyboards/_impl.py`
- `crm2/keyboards/admin_attendance.py`
- `crm2/keyboards/admin_panel.py`
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
- `BOT_TOKEN=1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`
- `ADMIN_ID=123456789`
- `WEATHER_API_KEY=your_openweather_api_key_here`
- `IGOR_KHOD_DEEPSEEK_API_KEY=sk-your-deepseek-key-here`
- `IGOR_OPENAI_API=sk-proj-your-openai-key-here`
- `LOG_LEVEL=INFO`
- `DEBUG_FULL_EXIT=0`
- `NOTIFY_STARTUP=1`
- `NOTIFY_SHUTDOWN=1`

## 🗄 Таблицы БД
(БД недоступна, используем DB_PATH=/var/data/crm.db)