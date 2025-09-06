# меняем PROJECT_MAP
# PROJECT_MAP — дополнение (список функций и глобальных переменных)

_Автоматически сгенерировано по архиву `crm2_250902_824.zip`. Описания: докстринги или эвристики._

## Врезка: исходный PROJECT_MAP.md

```
# 📂 PROJECT_MAP.md — карта проекта CRM2 (enriched)

**Автоматически дополнено перечнем функций и классов по каждому файлу из архива `crm2_250901_951.zip`.**

## Исходный PROJECT_MAP.md

```

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


```

## 🔎 Функции и классы по файлам

### `crm2/__init__.py`
- **Классы (0):** —
- **Функции (0):** —

### `crm2/__main__.py`
- **Классы (0):** —
- **Функции (0):** —

### `crm2/app.py`
- **Классы (0):** —
- **Функции (2):** try_include, main

### `crm2/cli_import_schedule.py`
- **Классы (0):** —
- **Функции (1):** main

### `crm2/config.py`
- **Классы (1):** Settings
- **Функции (1):** get_settings

### `crm2/db/__init__.py`
- **Классы (0):** —
- **Функции (0):** —

### `crm2/db/attendance.py`
- **Классы (0):** —
- **Функции (3):** get_last_attendance, get_summary, _table_exists

### `crm2/db/auto_migrate.py`
- **Классы (0):** —
- **Функции (7):** _exec, _has_column, ensure_topics_and_session_days, ensure_events_and_healings, ensure_user_flags_and_attendance, ensure_schedule_schema, ensure_all_schemas

### `crm2/db/bootstrap.py`
- **Классы (0):** —
- **Функции (1):** ensure_min_schema

### `crm2/db/content_loader.py`
- **Классы (0):** —
- **Функции (2):** _parse_md, sync_content_from_files

### `crm2/db/core.py`
- **Классы (0):** —
- **Функции (1):** get_db_connection

### `crm2/db/events.py`
- **Классы (0):** —
- **Функции (1):** upcoming_events_count

### `crm2/db/migrate_admin.py`
- **Классы (0):** —
- **Функции (1):** ensure_admin_schema

### `crm2/db/schedule_loader.py`
- **Классы (1):** Row
- **Функции (7):** _norm, _pick, _detect_cohort_from_filename, _iter_xlsx, sync_schedule_from_files, list_schedule_files, sync_schedule_autodiscover

### `crm2/db/schedule_repo.py`
- **Классы (0):** —
- **Функции (9):** _dicts, count_trainings, list_trainings, count_events, list_events, count_healings, list_healings, count_all, list_all

### `crm2/db/sqlite.py`
- **Классы (0):** —
- **Функции (6):** _query_only_enabled, _apply_pragmas_sync, _apply_pragmas_async, get_db_connection, aget_db_connection, ensure_schema

### `crm2/db/users.py`
- **Классы (0):** —
- **Функции (9):** get_db_connection, _row_to_dict, list_users, list_users_by_role, list_users_by_cohort, get_user_by_tg, get_user_by_nickname, delete_user_by_tg, upsert_user

### `crm2/db/users_repo.py`
- **Классы (0):** —
- **Функции (6):** _users_columns, _cohort_expr, _where_for_group, _row_to_dict, count_users, list_users

### `crm2/handlers/about.py`
- **Классы (0):** —
- **Функции (1):** cmd_about

### `crm2/handlers/admin/broadcast.py`
- **Классы (1):** BroadcastFSM
- **Функции (14):** audience_kb, cohorts_kb, confirm_kb, start_broadcast, choose_audience, set_cohort, set_text, no_attach, with_attach, preview, back_to_text, do_send, cancel_bc, back_bc

### `crm2/handlers/admin/logs.py`
- **Классы (0):** —
- **Функции (2):** logs_menu_kb, logs_overview

### `crm2/handlers/admin/panel.py`
- **Классы (0):** —
- **Функции (11):** _admin_menu_kb, admin_panel_kb, render_admin_panel, admin_entry_msg, admin_open_cb, admin_users_entry, admin_schedule_entry, admin_broadcast_entry, admin_logs_entry, admin_dbdoctor_entry, admin_dbdoctor_entry_text

### `crm2/handlers/admin/schedule.py`
- **Классы (0):** —
- **Функции (15):** schedule_menu, _render_menu, trainings_entry, trainings_cohort, trainings_page, _render_trainings, events_entry, events_page, _render_events, healings_entry, healings_page, _render_healings, all_entry, all_page, _render_all

### `crm2/handlers/admin/users.py`
- **Классы (0):** —
- **Функции (8):** admin_users_entry, admin_users_groups, _group_human, _user_line, _show_group_page, admin_users_pick_group, admin_users_page, admin_back

### `crm2/handlers/admin_db.py`
- **Классы (0):** —
- **Функции (2):** db_sessions_info, db_fix_cohort

### `crm2/handlers/admin_db_doctor.py`
- **Классы (0):** —
- **Функции (7):** show_menu, action_sessions_info, action_fix_sessions, action_indexes, action_become_guest, action_become_user2, back_to_main

### `crm2/handlers/admin_users.py`
- **Классы (0):** —
- **Функции (2):** admin_users_entry, admin_users_pick_group

### `crm2/handlers/attendance.py`
- **Классы (1):** AttStates
- **Функции (10):** attendance_entry, pick_cohort, show_cohort_sessions, enter_attendance, enter_payments, on_pick_session, _mark_kb_att, _mark_kb_pay, mark_attendance, mark_payment

### `crm2/handlers/auth.py`
- **Классы (1):** LoginSG
- **Функции (11):** _normalize, _is_bcrypt, _check_password, _human_name, _user_role, _bind_telegram_id, _fetch_user_by_credentials, cmd_login, login_nickname, login_password, _show_role_keyboard

### `crm2/handlers/consent.py`
- **Классы (0):** —
- **Функции (4):** consent_kb, has_consent, set_consent, agree

### `crm2/handlers/help.py`
- **Классы (0):** —
- **Функции (1):** cmd_help

### `crm2/handlers/info.py`
- **Классы (0):** —
- **Функции (14):** _get, _code, _fmt_date, _build_details_kb, show_schedule, session_details, show_agents, open_meditation, open_harmony, open_agents_instruction, back_to_main, show_project_menu, how_sessions_go, back_to_main_from_project

### `crm2/handlers/profile.py`
- **Классы (0):** —
- **Функции (4):** _get_user_row, show_profile, toggle_notify, my_materials

### `crm2/handlers/registration.py`
- **Классы (1):** RegistrationFSM
- **Функции (4):** start_registration_cb, reg_full_name, reg_phone, reg_email

### `crm2/handlers/start.py`
- **Классы (0):** —
- **Функции (2):** guest_menu_kb, cmd_start

### `crm2/handlers/welcome.py`
- **Классы (0):** —
- **Функции (2):** _user_exists, greet_new_user

### `crm2/handlers_schedule.py`
- **Классы (0):** —
- **Функции (10):** send_schedule_keyboard, send_nearest_session, _info_menu_kb, show_info_menu, _show_cohort1, _show_cohort2, _show_new, _show_all_schedule, _show_main_menu, on_session_click

### `crm2/keyboards/__init__.py`
- **Классы (0):** —
- **Функции (0):** —

### `crm2/keyboards/_impl.py`
- **Классы (0):** —
- **Функции (3):** guest_kb, role_kb, guest_start_kb

### `crm2/keyboards/admin_attendance.py`
- **Классы (0):** —
- **Функции (1):** choose_cohort_kb

### `crm2/keyboards/admin_schedule.py`
- **Классы (0):** —
- **Функции (3):** schedule_menu_kb, schedule_cohorts_kb, pager_kb

### `crm2/keyboards/admin_users.py`
- **Классы (0):** —
- **Функции (2):** users_groups_kb, users_pager_kb

### `crm2/keyboards/agents.py`
- **Классы (0):** —
- **Функции (1):** agents_menu_kb

### `crm2/keyboards/info_menu.py`
- **Классы (0):** —
- **Функции (1):** info_menu_kb

### `crm2/keyboards/main_menu.py`
- **Классы (0):** —
- **Функции (1):** main_menu_kb

### `crm2/keyboards/profile.py`
- **Классы (0):** —
- **Функции (1):** profile_menu_kb

### `crm2/keyboards/project.py`
- **Классы (0):** —
- **Функции (1):** project_menu_kb

### `crm2/keyboards/schedule.py`
- **Классы (0):** —
- **Функции (3):** _fmt_date, format_range, build_schedule_keyboard

### `crm2/keyboards/session_picker.py`
- **Классы (0):** —
- **Функции (1):** build_session_picker

### `crm2/logging_config.py`
- **Классы (0):** —
- **Функции (1):** setup_logging

### `crm2/routers/__init__.py`
- **Классы (0):** —
- **Функции (0):** —

### `crm2/routers/start.py`
- **Классы (0):** —
- **Функции (2):** get_user_role, cmd_start

### `crm2/services/schedule.py`
- **Классы (1):** Session
- **Функции (11):** _norm, _parse_date, _find_header_row, _cohort_id_from_filename, _load_one_file, load_all, get_user_cohort_id, upcoming, format_next, format_sessions_brief, next_training_text_for_user

### `crm2/services/services.py`
- **Классы (0):** —
- **Функции (0):** —

### `crm2/services/users.py`
- **Классы (0):** —
- **Функции (9):** _now_iso, ensure_user, classify_role, set_role, get_user_by_telegram, verify_password, get_user_cohort_id_by_tg, get_user_cohort_title_by_tg, get_user_cohort_code_by_tg

### `crm2/states.py`
- **Классы (1):** Login
- **Функции (0):** —

### `crm2/tools/sync_events_xlsx.py`
- **Классы (0):** —
- **Функции (5):** pick, to_iso, ensure_schema, sync_one_file, main

### `crm2/utils/guards.py`
- **Классы (1):** AdminOnly
- **Функции (0):** —

## ⚠️ Ошибки разбора некоторых файлов
- `crm2/db/sessions.py`: SyntaxError("f-string: expecting '}'", ('crm2/db/sessions.py', 340, 71, '            sql = f"SELECT {id_col} AS id, {start_col} AS start_date, {end_col or start_col} AS end_date, " \\\n                  f"{(topic_col + \' AS topic_code\') if topic_col else \'NULL AS topic_code\'}, " \\\n                  f"{(title_col + \' AS title\') if title_col else \'NULL AS title\'}, " \\\n                  f"{(ann_col + \' AS annotation\') if ann_col else "\'\' AS annotation"} " \\\n', 340, 73))
```

## 🔧 Функции по файлам

### `crm2/app.py`
- **main** — Точка запуска/инициализации (Сборка приложения).  
  _Файл_: `crm2/app.py` · _Назначение_: Сборка приложения
- **try_include** — Безопасно подключает роутер из модуля, если модуль/атрибут есть.  
  _Файл_: `crm2/app.py` · _Назначение_: Сборка приложения

### `crm2/cli_import_schedule.py`
- **main** — Точка запуска/инициализации (Прочее).  
  _Файл_: `crm2/cli_import_schedule.py` · _Назначение_: Прочее

### `crm2/config.py`
- **get_settings** — Получение данных (Конфигурация).  
  _Файл_: `crm2/config.py` · _Назначение_: Конфигурация

### `crm2/db/attendance.py`
- **_table_exists** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/attendance.py` · _Назначение_: Доступ к БД/DAO
- **get_last_attendance** — Возвращает последние limit записей по посещаемости пользователя:  
  _Файл_: `crm2/db/attendance.py` · _Назначение_: Доступ к БД/DAO
- **get_summary** — Возвращает кортеж: (present, absent, late) всего по пользователю.  
  _Файл_: `crm2/db/attendance.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/auto_migrate.py`
- **_exec** — Вспомогательный безопасный EXEC (без несуществующих cur).  
  _Файл_: `crm2/db/auto_migrate.py` · _Назначение_: Доступ к БД/DAO
- **_has_column** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/auto_migrate.py` · _Назначение_: Доступ к БД/DAO
- **ensure_all_schemas** — Единая точка: создаём всё, что нужно боту.  
  _Файл_: `crm2/db/auto_migrate.py` · _Назначение_: Доступ к БД/DAO
- **ensure_events_and_healings** — Гарантированное наличие/апсерт (Доступ к БД/DAO).  
  _Файл_: `crm2/db/auto_migrate.py` · _Назначение_: Доступ к БД/DAO
- **ensure_schedule_schema** — Поддержка старого имени: создаёт базовые таблицы расписания.  
  _Файл_: `crm2/db/auto_migrate.py` · _Назначение_: Доступ к БД/DAO
- **ensure_topics_and_session_days** — Гарантированное наличие/апсерт (Доступ к БД/DAO).  
  _Файл_: `crm2/db/auto_migrate.py` · _Назначение_: Доступ к БД/DAO
- **ensure_user_flags_and_attendance** — Гарантированное наличие/апсерт (Доступ к БД/DAO).  
  _Файл_: `crm2/db/auto_migrate.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/bootstrap.py`
- **ensure_min_schema** — Ensure core tables exist on startup (idempotent).  
  _Файл_: `crm2/db/bootstrap.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/content_loader.py`
- **_parse_md** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/content_loader.py` · _Назначение_: Доступ к БД/DAO
- **sync_content_from_files** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/content_loader.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/core.py`
- **get_db_connection** — Получение данных (Доступ к БД/DAO).  
  _Файл_: `crm2/db/core.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/events.py`
- **upcoming_events_count** — Вернёт количество будущих мероприятий (date >= сегодня).  
  _Файл_: `crm2/db/events.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/migrate_admin.py`
- **ensure_admin_schema** — Гарантированное наличие/апсерт (Доступ к БД/DAO).  
  _Файл_: `crm2/db/migrate_admin.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/schedule_loader.py`
- **_detect_cohort_from_filename** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_loader.py` · _Назначение_: Доступ к БД/DAO
- **_iter_xlsx** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_loader.py` · _Назначение_: Доступ к БД/DAO
- **_norm** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_loader.py` · _Назначение_: Доступ к БД/DAO
- **_pick** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_loader.py` · _Назначение_: Доступ к БД/DAO
- **list_schedule_files** — Находит реально существующие XLSX расписания по шаблону schedule_*_cohort.xlsx  
  _Файл_: `crm2/db/schedule_loader.py` · _Назначение_: Доступ к БД/DAO
- **sync_schedule_autodiscover** — Автоматически находит XLSX и загружает расписание.  
  _Файл_: `crm2/db/schedule_loader.py` · _Назначение_: Доступ к БД/DAO
- **sync_schedule_from_files** — XLSX с колонками: No | start_date | end_date | topic_code | title | annotation  
  _Файл_: `crm2/db/schedule_loader.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/schedule_repo.py`
- **_dicts** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_repo.py` · _Назначение_: Доступ к БД/DAO
- **count_all** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_repo.py` · _Назначение_: Доступ к БД/DAO
- **count_events** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_repo.py` · _Назначение_: Доступ к БД/DAO
- **count_healings** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_repo.py` · _Назначение_: Доступ к БД/DAO
- **count_trainings** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_repo.py` · _Назначение_: Доступ к БД/DAO
- **list_all** — Список/перечень сущностей (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_repo.py` · _Назначение_: Доступ к БД/DAO
- **list_events** — Список/перечень сущностей (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_repo.py` · _Назначение_: Доступ к БД/DAO
- **list_healings** — Список/перечень сущностей (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_repo.py` · _Назначение_: Доступ к БД/DAO
- **list_trainings** — Список/перечень сущностей (Доступ к БД/DAO).  
  _Файл_: `crm2/db/schedule_repo.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/sqlite.py`
- **_apply_pragmas_async** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/sqlite.py` · _Назначение_: Доступ к БД/DAO
- **_apply_pragmas_sync** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/sqlite.py` · _Назначение_: Доступ к БД/DAO
- **_query_only_enabled** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/sqlite.py` · _Назначение_: Доступ к БД/DAO
- **aget_db_connection** — Асинхронное подключение (aiosqlite).  
  _Файл_: `crm2/db/sqlite.py` · _Назначение_: Доступ к БД/DAO
- **ensure_schema** — Идемпотентно создаёт базовые таблицы. ВАЖНО: всегда открываем соединение  
  _Файл_: `crm2/db/sqlite.py` · _Назначение_: Доступ к БД/DAO
- **get_db_connection** — Синхронное подключение.  
  _Файл_: `crm2/db/sqlite.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/users.py`
- **_row_to_dict** — Преобразует sqlite3.Row в dict.  
  _Файл_: `crm2/db/users.py` · _Назначение_: Доступ к БД/DAO
- **delete_user_by_tg** — Удаляет пользователя по telegram_id.  
  _Файл_: `crm2/db/users.py` · _Назначение_: Доступ к БД/DAO
- **get_db_connection** — Открывает соединение с SQLite с row_factory=sqlite3.Row.  
  _Файл_: `crm2/db/users.py` · _Назначение_: Доступ к БД/DAO
- **get_user_by_nickname** — Возвращает пользователя по nickname.  
  _Файл_: `crm2/db/users.py` · _Назначение_: Доступ к БД/DAO
- **get_user_by_tg** — Возвращает пользователя по telegram_id.  
  _Файл_: `crm2/db/users.py` · _Назначение_: Доступ к БД/DAO
- **list_users** — Возвращает список всех пользователей.  
  _Файл_: `crm2/db/users.py` · _Назначение_: Доступ к БД/DAO
- **list_users_by_cohort** — Возвращает список пользователей по cohort_id.  
  _Файл_: `crm2/db/users.py` · _Назначение_: Доступ к БД/DAO
- **list_users_by_role** — Возвращает список пользователей по роли.  
  _Файл_: `crm2/db/users.py` · _Назначение_: Доступ к БД/DAO
- **upsert_user** — Создаёт пользователя, если его нет; иначе — обновляет непустые поля.  
  _Файл_: `crm2/db/users.py` · _Назначение_: Доступ к БД/DAO

### `crm2/db/users_repo.py`
- **_cohort_expr** — Возвращает корректное SQL-выражение для 'потока':  
  _Файл_: `crm2/db/users_repo.py` · _Назначение_: Доступ к БД/DAO
- **_row_to_dict** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/users_repo.py` · _Назначение_: Доступ к БД/DAO
- **_users_columns** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/users_repo.py` · _Назначение_: Доступ к БД/DAO
- **_where_for_group** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/users_repo.py` · _Назначение_: Доступ к БД/DAO
- **count_users** — Функция модуля (Доступ к БД/DAO).  
  _Файл_: `crm2/db/users_repo.py` · _Назначение_: Доступ к БД/DAO
- **list_users** — Список/перечень сущностей (Доступ к БД/DAO).  
  _Файл_: `crm2/db/users_repo.py` · _Назначение_: Доступ к БД/DAO

### `crm2/handlers/about.py`
- **cmd_about** — Обработчик события/команды (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/about.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/admin/broadcast.py`
- **audience_kb** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **back_bc** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **back_to_text** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **cancel_bc** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **choose_audience** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **cohorts_kb** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **confirm_kb** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **do_send** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **no_attach** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **preview** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **set_cohort** — Обновление записи (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **set_text** — Обновление записи (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **start_broadcast** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм
- **with_attach** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/broadcast.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/admin/logs.py`
- **logs_menu_kb** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/logs.py` · _Назначение_: Хендлеры/айограм
- **logs_overview** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/logs.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/admin/panel.py`
- **_admin_menu_kb** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм
- **admin_broadcast_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм
- **admin_dbdoctor_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм
- **admin_dbdoctor_entry_text** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм
- **admin_entry_msg** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм
- **admin_logs_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм
- **admin_open_cb** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм
- **admin_panel_kb** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм
- **admin_schedule_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм
- **admin_users_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм
- **render_admin_panel** — Форматирование/рендер (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/panel.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/admin/schedule.py`
- **_render_all** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **_render_events** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **_render_healings** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **_render_menu** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **_render_trainings** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **all_entry** — Список/перечень сущностей (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **all_page** — Список/перечень сущностей (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **events_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **events_page** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **healings_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **healings_page** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **schedule_menu** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **trainings_cohort** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **trainings_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм
- **trainings_page** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/schedule.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/admin/users.py`
- **_group_human** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/users.py` · _Назначение_: Хендлеры/айограм
- **_show_group_page** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/users.py` · _Назначение_: Хендлеры/айограм
- **_user_line** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/users.py` · _Назначение_: Хендлеры/айограм
- **admin_back** — Возврат из списка пользователей в админ-панель.  
  _Файл_: `crm2/handlers/admin/users.py` · _Назначение_: Хендлеры/айограм
- **admin_users_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/users.py` · _Назначение_: Хендлеры/айограм
- **admin_users_groups** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/users.py` · _Назначение_: Хендлеры/айограм
- **admin_users_page** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/users.py` · _Назначение_: Хендлеры/айограм
- **admin_users_pick_group** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin/users.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/admin_db.py`
- **db_fix_cohort** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_db.py` · _Назначение_: Хендлеры/айограм
- **db_sessions_info** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_db.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/admin_db_doctor.py`
- **action_become_guest** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_db_doctor.py` · _Назначение_: Хендлеры/айограм
- **action_become_user2** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_db_doctor.py` · _Назначение_: Хендлеры/айограм
- **action_fix_sessions** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_db_doctor.py` · _Назначение_: Хендлеры/айограм
- **action_indexes** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_db_doctor.py` · _Назначение_: Хендлеры/айограм
- **action_sessions_info** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_db_doctor.py` · _Назначение_: Хендлеры/айограм
- **back_to_main** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_db_doctor.py` · _Назначение_: Хендлеры/айограм
- **show_menu** — Отправка/показ интерфейса (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_db_doctor.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/admin_users.py`
- **admin_users_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_users.py` · _Назначение_: Хендлеры/айограм
- **admin_users_pick_group** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/admin_users.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/attendance.py`
- **_mark_kb_att** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/attendance.py` · _Назначение_: Хендлеры/айограм
- **_mark_kb_pay** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/attendance.py` · _Назначение_: Хендлеры/айограм
- **attendance_entry** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/attendance.py` · _Назначение_: Хендлеры/айограм
- **enter_attendance** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/attendance.py` · _Назначение_: Хендлеры/айограм
- **enter_payments** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/attendance.py` · _Назначение_: Хендлеры/айограм
- **mark_attendance** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/attendance.py` · _Назначение_: Хендлеры/айограм
- **mark_payment** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/attendance.py` · _Назначение_: Хендлеры/айограм
- **on_pick_session** — Обработчик события/команды (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/attendance.py` · _Назначение_: Хендлеры/айограм
- **pick_cohort** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/attendance.py` · _Назначение_: Хендлеры/айограм
- **show_cohort_sessions** — Отправка/показ интерфейса (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/attendance.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/auth.py`
- **_bind_telegram_id** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм
- **_check_password** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм
- **_fetch_user_by_credentials** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм
- **_human_name** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм
- **_is_bcrypt** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм
- **_normalize** — Убираем неразрывные/невидимые пробелы и обрезаем края.  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм
- **_show_role_keyboard** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм
- **_user_role** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм
- **cmd_login** — Обработчик события/команды (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм
- **login_nickname** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм
- **login_password** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/auth.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/consent.py`
- **agree** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/consent.py` · _Назначение_: Хендлеры/айограм
- **consent_kb** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/consent.py` · _Назначение_: Хендлеры/айограм
- **has_consent** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/consent.py` · _Назначение_: Хендлеры/айограм
- **set_consent** — Обновление записи (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/consent.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/help.py`
- **cmd_help** — Обработчик события/команды (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/help.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/info.py`
- **_build_details_kb** — Кнопки-строки: ДАТЫ + индекс курса.  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **_code** — Берём индекс занятия по любому из возможных имён поля.  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **_fmt_date** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **_get** — Достаёт поле и у объекта, и у dict.  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **back_to_main** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **back_to_main_from_project** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **how_sessions_go** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **open_agents_instruction** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **open_harmony** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **open_meditation** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **session_details** — Карточка занятия: даты, код, тема и аннотация.  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **show_agents** — Отправка/показ интерфейса (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **show_project_menu** — Отправка/показ интерфейса (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм
- **show_schedule** — Список занятий: даты + индекс в скобках; кнопки — даты + индекс.  
  _Файл_: `crm2/handlers/info.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/profile.py`
- **_get_user_row** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/profile.py` · _Назначение_: Хендлеры/айограм
- **my_materials** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/profile.py` · _Назначение_: Хендлеры/айограм
- **show_profile** — Отправка/показ интерфейса (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/profile.py` · _Назначение_: Хендлеры/айограм
- **toggle_notify** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/profile.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/registration.py`
- **reg_email** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/registration.py` · _Назначение_: Хендлеры/айограм
- **reg_full_name** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/registration.py` · _Назначение_: Хендлеры/айограм
- **reg_phone** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/registration.py` · _Назначение_: Хендлеры/айограм
- **start_registration_cb** — Старт из инлайн-кнопки (гостевое меню).  
  _Файл_: `crm2/handlers/registration.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/start.py`
- **cmd_start** — Разводим новых и существующих пользователей:  
  _Файл_: `crm2/handlers/start.py` · _Назначение_: Хендлеры/айограм
- **guest_menu_kb** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/start.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers/welcome.py`
- **_user_exists** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/welcome.py` · _Назначение_: Хендлеры/айограм
- **greet_new_user** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers/welcome.py` · _Назначение_: Хендлеры/айограм

### `crm2/handlers_schedule.py`
- **_info_menu_kb** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers_schedule.py` · _Назначение_: Хендлеры/айограм
- **_show_all_schedule** — Смешанное расписание всех потоков, сортированное по дате начала  
  _Файл_: `crm2/handlers_schedule.py` · _Назначение_: Хендлеры/айограм
- **_show_cohort1** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers_schedule.py` · _Назначение_: Хендлеры/айограм
- **_show_cohort2** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers_schedule.py` · _Назначение_: Хендлеры/айограм
- **_show_main_menu** — Возврат в главное меню  
  _Файл_: `crm2/handlers_schedule.py` · _Назначение_: Хендлеры/айограм
- **_show_new** — Функция модуля (Хендлеры/айограм).  
  _Файл_: `crm2/handlers_schedule.py` · _Назначение_: Хендлеры/айограм
- **on_session_click** — Обработчик события/команды (Хендлеры/айограм).  
  _Файл_: `crm2/handlers_schedule.py` · _Назначение_: Хендлеры/айограм
- **send_nearest_session** — Шлёт ТОЛЬКО одну строку «Ближайшее занятие: …», без клавиатуры.  
  _Файл_: `crm2/handlers_schedule.py` · _Назначение_: Хендлеры/айограм
- **send_schedule_keyboard** — Renders:  
  _Файл_: `crm2/handlers_schedule.py` · _Назначение_: Хендлеры/айограм
- **show_info_menu** — Отправка/показ интерфейса (Хендлеры/айограм).  
  _Файл_: `crm2/handlers_schedule.py` · _Назначение_: Хендлеры/айограм

### `crm2/keyboards/_impl.py`
- **guest_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/_impl.py` · _Назначение_: Клавиатуры/интерфейс
- **guest_start_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/_impl.py` · _Назначение_: Клавиатуры/интерфейс
- **role_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/_impl.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/keyboards/admin_attendance.py`
- **choose_cohort_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/admin_attendance.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/keyboards/admin_schedule.py`
- **pager_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/admin_schedule.py` · _Назначение_: Клавиатуры/интерфейс
- **schedule_cohorts_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/admin_schedule.py` · _Назначение_: Клавиатуры/интерфейс
- **schedule_menu_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/admin_schedule.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/keyboards/admin_users.py`
- **users_groups_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/admin_users.py` · _Назначение_: Клавиатуры/интерфейс
- **users_pager_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/admin_users.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/keyboards/agents.py`
- **agents_menu_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/agents.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/keyboards/info_menu.py`
- **info_menu_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/info_menu.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/keyboards/main_menu.py`
- **main_menu_kb** — Главное пользовательское меню.  
  _Файл_: `crm2/keyboards/main_menu.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/keyboards/profile.py`
- **profile_menu_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/profile.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/keyboards/project.py`
- **project_menu_kb** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/project.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/keyboards/schedule.py`
- **_fmt_date** — Функция модуля (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/schedule.py` · _Назначение_: Клавиатуры/интерфейс
- **build_schedule_keyboard** — sessions: iterable of dicts with keys: id, start_date, end_date, topic_code, cohort_id  
  _Файл_: `crm2/keyboards/schedule.py` · _Назначение_: Клавиатуры/интерфейс
- **format_range** — Форматирование/рендер (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/schedule.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/keyboards/session_picker.py`
- **build_session_picker** — Построение структуры/объекта (Клавиатуры/интерфейс).  
  _Файл_: `crm2/keyboards/session_picker.py` · _Назначение_: Клавиатуры/интерфейс

### `crm2/logging_config.py`
- **setup_logging** — Функция модуля (Прочее).  
  _Файл_: `crm2/logging_config.py` · _Назначение_: Прочее

### `crm2/routers/start.py`
- **cmd_start** — Обработчик события/команды (Прочее).  
  _Файл_: `crm2/routers/start.py` · _Назначение_: Прочее
- **get_user_role** — Получение данных (Прочее).  
  _Файл_: `crm2/routers/start.py` · _Назначение_: Прочее

### `crm2/services/schedule.py`
- **_cohort_id_from_filename** — Вытаскиваем id потока из имени файла вида '... 1 поток.xlsx' или '... 2 поток.xlsx'.  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика
- **_find_header_row** — Возвращает (row_index, mapping), где mapping — словарь с индексами нужных колонок.  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика
- **_load_one_file** — Функция модуля (Сервисный слой/бизнес-логика).  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика
- **_norm** — Функция модуля (Сервисный слой/бизнес-логика).  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика
- **_parse_date** — Поддержка datetime/date и строковых форматов 'YYYY-MM-DD' или 'DD.MM.YYYY'.  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика
- **format_next** — Форматирование/рендер (Сервисный слой/бизнес-логика).  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика
- **format_sessions_brief** — Форматирование/рендер (Сервисный слой/бизнес-логика).  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика
- **get_user_cohort_id** — Получение данных (Сервисный слой/бизнес-логика).  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика
- **load_all** — Читает все файлы вида 'расписание *.xlsx' из crm2/data и  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика
- **next_training_text_for_user** — Текст «ближайшего занятия» (или пустая строка, если нет данных/потока).  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика
- **upcoming** — Ближайшие (не прошедшие) сессии для пользователя по его потоку.  
  _Файл_: `crm2/services/schedule.py` · _Назначение_: Сервисный слой/бизнес-логика

### `crm2/services/users.py`
- **_now_iso** — Функция модуля (Сервисный слой/бизнес-логика).  
  _Файл_: `crm2/services/users.py` · _Назначение_: Сервисный слой/бизнес-логика
- **classify_role** — Вернёт читабельное название роли  
  _Файл_: `crm2/services/users.py` · _Назначение_: Сервисный слой/бизнес-логика
- **ensure_user** — Создаёт гостя при первом заходе; обновляет last_seen при следующих.  
  _Файл_: `crm2/services/users.py` · _Назначение_: Сервисный слой/бизнес-логика
- **get_user_by_telegram** — Вернёт всю запись пользователя как dict по telegram_id,  
  _Файл_: `crm2/services/users.py` · _Назначение_: Сервисный слой/бизнес-логика
- **get_user_cohort_code_by_tg** — Совместимость с существующими вызовами.  
  _Файл_: `crm2/services/users.py` · _Назначение_: Сервисный слой/бизнес-логика
- **get_user_cohort_id_by_tg** — Возвращает cohort_id пользователя по его Telegram ID, если он есть в participants.  
  _Файл_: `crm2/services/users.py` · _Назначение_: Сервисный слой/бизнес-логика
- **get_user_cohort_title_by_tg** — Возвращает название потока (cohorts.title) пользователя по его Telegram ID.  
  _Файл_: `crm2/services/users.py` · _Назначение_: Сервисный слой/бизнес-логика
- **set_role** — Обновляет роль пользователя  
  _Файл_: `crm2/services/users.py` · _Назначение_: Сервисный слой/бизнес-логика
- **verify_password** — Возвращает True, если в таблице users есть запись с таким nickname и password.  
  _Файл_: `crm2/services/users.py` · _Назначение_: Сервисный слой/бизнес-логика

### `crm2/tools/sync_events_xlsx.py`
- **ensure_schema** — Гарантированное наличие/апсерт (Прочее).  
  _Файл_: `crm2/tools/sync_events_xlsx.py` · _Назначение_: Прочее
- **main** — Точка запуска/инициализации (Прочее).  
  _Файл_: `crm2/tools/sync_events_xlsx.py` · _Назначение_: Прочее
- **pick** — Функция модуля (Прочее).  
  _Файл_: `crm2/tools/sync_events_xlsx.py` · _Назначение_: Прочее
- **sync_one_file** — Функция модуля (Прочее).  
  _Файл_: `crm2/tools/sync_events_xlsx.py` · _Назначение_: Прочее
- **to_iso** — Функция модуля (Прочее).  
  _Файл_: `crm2/tools/sync_events_xlsx.py` · _Назначение_: Прочее

## 🌍 Глобальные переменные проекта

| Переменная | Значение (если константа) | Файл |
|---|---|---|
| `ADMIN_ID` | — | `crm2/app.py` |
| `ANN_COLS` | — | `crm2/tools/sync_events_xlsx.py` |
| `ANN_HEADERS` | — | `crm2/services/schedule.py` |
| `BASE_DIR` | — | `crm2/config.py` |
| `BOT_TOKEN` | — | `crm2/app.py` |
| `BTN_BACK` | '↩️ Главное меню' | `crm2/handlers/admin_db_doctor.py` |
| `BTN_BECOME_GUEST` | '🙈 Стать гостем' | `crm2/handlers/admin_db_doctor.py` |
| `BTN_BECOME_USER2` | '👤 Стать user поток 2' | `crm2/handlers/admin_db_doctor.py` |
| `BTN_FIX` | '🛠 Исправить sessions' | `crm2/handlers/admin_db_doctor.py` |
| `BTN_INDEXES` | '📂 Индексы' | `crm2/handlers/admin_db_doctor.py` |
| `BTN_STRUCT` | '📊 Структура БД' | `crm2/handlers/admin_db_doctor.py` |
| `CODE_COLS` | — | `crm2/tools/sync_events_xlsx.py` |
| `CODE_HEADERS` | — | `crm2/services/schedule.py` |
| `CONSENT_TEXT` | 'При отправке номера телефона и email при регистрации вы даёте согласие на обработку персональных данных https://krasnpsytech.ru/ZQFHN32\nНажимая на кнопку «Соглашаюсь», вы соглашаетесь получать информационные сообщения. Отказаться можно в любой момент 👌' | `crm2/handlers/consent.py` |
| `DATA_DIR` | — | `crm2/services/schedule.py` |
| `DATE_COLS` | — | `crm2/tools/sync_events_xlsx.py` |
| `DB_PATH` | — | `crm2/db/sqlite.py` |
| `DB_PATH` | — | `crm2/tools/sync_events_xlsx.py` |
| `END_COLS` | — | `crm2/tools/sync_events_xlsx.py` |
| `END_HEADERS` | — | `crm2/services/schedule.py` |
| `GROUPS` | — | `crm2/keyboards/admin_users.py` |
| `H1_RE` | — | `crm2/db/content_loader.py` |
| `HEADER_SCAN_ROWS` | 10 | `crm2/services/schedule.py` |
| `ISO_RE` | — | `crm2/db/schedule_loader.py` |
| `PAGE` | 10 | `crm2/handlers/admin/schedule.py` |
| `PAGE_SIZE` | 10 | `crm2/handlers/admin/users.py` |
| `PROJECT_DIR` | — | `crm2/db/schedule_loader.py` |
| `REG_START` | 'registration:start' | `crm2/handlers/registration.py` |
| `SCHEDULE_DIR` | — | `crm2/tools/sync_events_xlsx.py` |
| `START_HEADERS` | — | `crm2/services/schedule.py` |
| `TITLE_COLS` | — | `crm2/tools/sync_events_xlsx.py` |
| `TITLE_HEADERS` | — | `crm2/services/schedule.py` |
| `_BCRYPT_RE` | — | `crm2/handlers/auth.py` |
| `_COL_SYNONYMS` | — | `crm2/db/schedule_loader.py` |

## 🌐 Переменные окружения (где читаются)

| ENV | Значение по умолчанию | Файл |
|---|---|---|
| `ADMIN_ID` | — | `crm2/app.py` |
| `ADMIN_ID` | — | `crm2/config.py` |
| `BOT_TOKEN` | — | `crm2/app.py` |
| `CRM_DB` | — | `crm2/config.py` |
| `CRM_DB_QUERY_ONLY` | 1 | `crm2/db/sqlite.py` |
| `DB_PATH` | crm.db | `crm2/tools/sync_events_xlsx.py` |
| `LOG_LEVEL` | — | `crm2/config.py` |
| `SCHEDULE_DIR` | /var/data/schedules | `crm2/tools/sync_events_xlsx.py` |
| `TELEGRAM_TOKEN` | — | `crm2/app.py` |
| `TELEGRAM_TOKEN` | — | `crm2/config.py` |
