# 📂 PROJECT_MAP.md — карта проекта CRM2

## 📁 Структура каталогов и файлов

```
crm2/
├── __main__.py           # Точка входа: запускает main() из app.py
├── app.py                # Главный цикл бота, регистрация роутеров
├── auto_migrate.py       # Автоматические миграции БД (создание таблиц, индексов)
├── db/                   # Работа с БД
│   ├── users.py          # CRUD для пользователей
│   ├── sessions.py       # CRUD для сессий и расписания
│   ├── attendance.py     # Учёт посещаемости
│   └── profile.py        # Профили пользователей
├── handlers/             # Обработчики команд и кнопок
│   ├── start.py          # /start, приветствие и вход
│   ├── auth.py           # Авторизация, вход/регистрация
│   ├── info.py           # Раздел «Информация»
│   ├── admin_users.py    # Администрирование пользователей
│   ├── admin_schedule.py # Управление расписанием
│   ├── admin_attendance.py # Учёт посещаемости (админ)
│   └── admin_db_doctor.py # Проверка/исправление БД («DB Doctor»)
├── keyboards/            # Inline/Reply клавиатуры
│   ├── main_menu.py      # Главное меню
│   ├── schedule.py       # Кнопки расписания
│   ├── profile.py        # Кнопки профиля
│   ├── agents.py         # Кнопки ИИ-агентов
│   └── admin_*           # Кнопки админских меню
└── utils/                # Утилиты и вспомогательные функции
```

---

## 🗄 Структура базы данных (crm.db)

### users
- id — PK
- telegram_id — уникальный ID TG
- username, nickname, full_name
- password — хэш
- role — роль (admin/user)
- phone, email
- events, participants
- cohort_id — связка с cohorts

### cohorts
- id, name

### participants
- id
- user_id — FK users.id
- cohort_id — FK cohorts.id
- stream_id — FK streams.id
- created_at

### streams
- id, title

### sessions
- id, start_date, end_date
- topic_code, title, annotation
- stream_id, cohort_id

### session_days
- id, date, stream_id, topic_id, topic_code

### topics
- id, code, title, annotation

### materials
- id, title, body, tg_file_id, mime, created_by, created_at

### assignments
- id, title, body, material_id, due_date, created_by, created_at

### broadcasts
- id, title, body, attachment, audience, cohort_id, status, etc.

### broadcast_recipients
- broadcast_id, user_id, status, sent_at

### consents
- telegram_id, given, ts

---

## 🔧 Ключевые функции по файлам

### db/users.py
- `get_user_by_tg()` — вернуть пользователя по telegram_id
- `add_user()` — регистрация нового
- `update_user_role()` — смена роли
- `list_users()` — список пользователей

### db/sessions.py
- `get_upcoming_sessions_by_cohort()` — ближайшие занятия для потока
- `get_all_sessions()` — общее расписание
- `add_session()` — добавить занятие

### db/attendance.py
- `mark_attendance()` — отметить посещение
- `get_attendance_by_user()` — посещаемость для профиля
- `get_attendance_by_cohort()` — журнал для потока

### handlers/start.py
- `cmd_start()` — обработка /start
- приветствие новых / переход в меню старых пользователей

### handlers/admin_db_doctor.py
- `show_menu()` — меню проверки БД
- `show_structure()` — показать таблицы/схему
- `fix_sessions()` — починить сессии (добавить cohort_id)
- `show_indexes()` — показать индексы

---
## Правила корректировок

Чтобы избежать ошибок и путаницы при изменениях, используется следующий протокол:

1. **Определение задачи**  
   - Сначала описывается, что нужно сделать или исправить.

2. **Список необходимых файлов**  
   - AI составляет список файлов, которые нужно прислать для анализа (например: `app.py`, `handlers/attendance.py`, `db/users.py`).

3. **Передача исходников**  
   - Пользователь присылает именно эти файлы из архива проекта.

4. **Корректировка**  
   - AI вносит изменения строго на основе предоставленных исходников, без догадок.

5. **Работа с базой данных**  
   - Если изменения затрагивают базу (`/var/data/crm.db`), AI отдельно запрашивает структуру таблиц (`.schema`) или использует актуальный `PROJECT_MAP.md`.

Такой подход гарантирует согласованность и исключает потерю времени из-за расхождений.
"""

[!] У Игоря есть собственные шпаргалки. Этот файл — карта проекта.

## ✅ Использование
Этот файл служит «картой» проекта.  
Перед изменениями сверяемся с ним, чтобы не вводить новые переменные (пример: `stream` → `cohort_id`).

