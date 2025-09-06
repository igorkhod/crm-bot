# PROJECT_MAP.full.md — Полная дорожная карта проекта Psytech CRM Bot

> Версия: 2025-09-06 • Проект: Psytech (aiogram 3.x) • БД: SQLite (/var/data/crm.db) • Репозиторий: [igorkhod/crm](https://github.com/igorkhod/crm)

---

## 1. Обзор проекта
Telegram-бот для управления потоками психотехнических тренировок.  
Роли: **guest**, **user**, **admin**, **cohort_1**, **cohort_2**, **new_intake**, **alumni**, **admins**.

---

## 2. Меню по ролям

### Guest
- 📖 О проекте (ReplyKeyboardRemove, без возврата в меню)
- (Нет кнопки «Главное меню»)

### User
- 📅 Расписание (≤5 ближайших дат; выбор → тема + описание)
- 📚 Материалы
- 👤 Личный кабинет
- 📊 Посещение
- ↩️ Главное меню

### Admin
- Всё как у User
- ⚙️ Админ-панель:
  - 🩺 DB Doctor
  - 👥 Пользователи (изменение ролей, блокировка)
  - 🗂 Управление потоками
  - 📢 Рассылка (broadcast)
  - 📜 Логи (admin_logs)
  - 📅 Управление расписанием (admin_schedule)

### Alumni
- Доступ к архиву материалов
- Ограниченный просмотр расписания

---

## 3. Переменные окружения (.env)

Файл: `/etc/psytech-bot.env` (на VPS)  
Примеры:
```
TELEGRAM_TOKEN=123456:ABCDEF
DB_PATH=/var/data/crm.db
LOG_LEVEL=INFO
VPS_HOST=185.23.34.161
VPS_USER=botuser
VPS_SSH_PORT=2222
```
(секреты GitHub: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_SSH_PORT`)

---

## 4. Таблицы БД

### users
- id (INTEGER, PK)
- telegram_id (INTEGER)
- nickname (TEXT, уникальный)
- password (TEXT, bcrypt hash)
- role (TEXT, default='user')
- cohort_id (INTEGER, FK → cohorts.id)
- full_name (TEXT)
- phone (TEXT)
- email (TEXT)

### cohorts
- id (INTEGER, PK)
- code (TEXT, уникальный: cohort_2023_09, cohort_2025_03 …)
- title (TEXT)

### session_days
- id (INTEGER, PK)
- date (DATE)
- cohort_id (INTEGER, FK)
- topic_code (TEXT, FK → topics.code)

### topics
- code (TEXT, PK)
- title (TEXT)
- annotation (TEXT)

### events (планируется)
- id, type, date, metadata

### payments (планируется)
- id, user_id, amount, status, date

---

## 5. Структура репозитория (ссылки на GitHub)

```
crm2/
 ├── __main__.py
 ├── app.py
 ├── handlers/
 │    ├── start.py
 │    ├── auth.py
 │    ├── registration.py
 │    ├── info.py
 │    ├── admin_users.py
 │    ├── admin_db.py
 │    └── handlers_schedule.py
 ├── keyboards/
 │    ├── main_menu.py
 │    └── __init__.py
 ├── services/
 │    └── schedule.py
 ├── db/
 │    ├── auto_migrate.py
 │    ├── schedule_loader.py
 │    └── users_repo.py
 └── PROJECT_MAP.full.md   ← этот файл
```

🔗 Прямые ссылки:  
- [`app.py`](https://github.com/igorkhod/crm/blob/main/crm2/app.py)  
- [`handlers/start.py`](https://github.com/igorkhod/crm/blob/main/crm2/handlers/start.py)  
- [`handlers/auth.py`](https://github.com/igorkhod/crm/blob/main/crm2/handlers/auth.py)  
- [`handlers/registration.py`](https://github.com/igorkhod/crm/blob/main/crm2/handlers/registration.py)  
- [`handlers/info.py`](https://github.com/igorkhod/crm/blob/main/crm2/handlers/info.py)  
- [`handlers/admin_users.py`](https://github.com/igorkhod/crm/blob/main/crm2/handlers/admin_users.py)  
- [`handlers/admin_db.py`](https://github.com/igorkhod/crm/blob/main/crm2/handlers/admin_db.py)  
- [`handlers/handlers_schedule.py`](https://github.com/igorkhod/crm/blob/main/crm2/handlers/handlers_schedule.py)  
- [`db/users_repo.py`](https://github.com/igorkhod/crm/blob/main/crm2/db/users_repo.py)  
- [`db/schedule_loader.py`](https://github.com/igorkhod/crm/blob/main/crm2/db/schedule_loader.py)  
- [`db/auto_migrate.py`](https://github.com/igorkhod/crm/blob/main/crm2/db/auto_migrate.py)  
- [`services/schedule.py`](https://github.com/igorkhod/crm/blob/main/crm2/services/schedule.py)

---

## 6. Инфраструктура

### Systemd-сервис
Файл: `/etc/systemd/system/psytech-bot.service`  
- Автозапуск: `/opt/psytech-bot/app`  
- Управление:
  ```bash
  sudo -n systemctl restart psytech-bot
  sudo -n systemctl status psytech-bot
  ```

### Admin-скрипт
Файл: `~/admin.sh`  
- Автобэкап `/var/data/crm.db`
- Назначение роли `admin` и потока:
  ```bash
  admin
  ```

### CI/CD (GitHub Actions)
Файл: `.github/workflows/deploy.yml`  
- При `git push main`:
  - заливает код на VPS
  - ставит зависимости
  - перезапускает сервис

---

## 7. Roadmap
- [x] Ограничение меню для guest (без «↩️ Главное меню»)
- [x] Настроен деплой GitHub → VPS (scp+ssh)
- [ ] Кнопки «Расписание»: ≤5 дат, при клике → тема и описание
- [ ] Учёт посещений и оплат
- [ ] Рассылка материалов оплатившим
- [ ] Админ-модули: schedule/logs/broadcast
- [ ] Webhook через Nginx+SSL (опционально)
