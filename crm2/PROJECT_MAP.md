# PROJECT_MAP.md

## Общая структура
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
 └── PROJECT_MAP.md   ← этот файл
```

---

## Роли пользователей
Список доступных ролей (enum в коде):  
- `cohort_1` — участники потока 1 (сентябрь 2023)  
- `cohort_2` — участники потока 2 (март 2025, включая донабор август 2025)  
- `new_intake` — новый поток (январь 2026)  
- `alumni` — выпускники  
- `admins` — администраторы  

> ⚠️ В базе поле `role` хранит одно из этих значений.  
> При логине роль подгружается из таблицы `users`.

---

## Основные модули

### `app.py`
- Инициализация бота, диспетчера.
- Подключение роутеров `handlers/*`.
- Авто-миграции БД (`db/auto_migrate.py`).

### `handlers/start.py`
- `/start` — приветствие.
- Кнопки: «Войти», «Зарегистрироваться».
- Для вошедших — «Админ-панель», «Информация».

### `handlers/auth.py`
- Вход по никнейму/паролю.
- Проверка через `users_repo.py`.
- Привязка к Telegram ID.

### `handlers/registration.py`
- Регистрация: никнейм, пароль, ФИО, телефон, email.
- Запись в таблицу `users`.

### `handlers/info.py`
- Вывод расписания.
- Кнопки по потокам → темы занятий.

### `handlers/admin_users.py`
- Панель управления пользователями.
- Изменение роли (`role` → `admins`, `cohort_1`, …).
- Блокировка / удаление пользователей.

### `handlers/admin_db.py`
- Диагностика БД, резервное копирование.
- Управление сессиями.

### `db/users_repo.py`
- CRUD-операции с таблицей `users`.
- Проверка логина/пароля.
- Методы `set_role()`, `set_cohort()`.

### `db/schedule_loader.py`
- Загрузка расписания из Excel (`schedule_2025_1_cohort.xlsx`, `schedule_2025_2_cohort.xlsx`).
- Заполнение таблиц `session_days`, `topics`.

---

## Инфраструктура

### Systemd-сервис
Файл: `/etc/systemd/system/psytech-bot.service`  
- Автозапуск бота из `/opt/psytech-bot/app`.  
- Управление:  
  ```bash
  sudo -n systemctl restart psytech-bot
  sudo -n systemctl status psytech-bot
  ```

### Admin-скрипт
Файл: `~/admin.sh`  
- Бэкап базы `/var/data/crm.db`  
- Повышение пользователя до admin:  
  ```bash
  admin
  ```

### CI/CD (GitHub Actions)
Файл: `.github/workflows/deploy.yml`  
- При `git push main`:  
  - упаковывает проект  
  - заливает на VPS  
  - перезапускает сервис  

Secrets:
- `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_SSH_PORT`.

---

## TODO
- [ ] Реализовать раздел «Материалы».  
- [ ] Реализовать учёт «Посещения».  
- [ ] Подключить массовую рассылку (broadcast).  
- [ ] Добавить «admin_logs» для журналов.  
- [ ] Добавить «admin_schedule» для управления расписанием.

### `handlers/info.py`
- Раздел «ℹ️ Информация о проекте».
- Показывает подменю с кнопками:
  - «Режим проведения занятий» (контент: `content/info/mode.md`)
  - «Смыслы, заложенные в проекте» (контент: `content/info/meanings.md`)
- Использует сервис `services/content_loader.py` для рендера Markdown.
# PROJECT_MAP.md

---

## app.py (экспорт bot & dp)
- Инициализирует **aiogram.Bot** из `TELEGRAM_TOKEN` (берётся из окружения; у прод-сервера — через `EnvironmentFile=/opt/psytech-bot/app/token.env` в systemd).
- Экспортирует:
  - `bot` — используется хендлерами для отправки сообщений.
  - `dp` — главный Dispatcher.
- Подключает роутеры из `crm2/handlers/*`, в том числе `admin_attendance.router`.

### handlers/admin_attendance.py
- Команда: `/homework_send <session_id> <ссылка>`
- Берёт список присутствовавших через `crm2/services/attendance.get_present_users(session_id)`.
- Импортирует бот так: `from crm2.app import bot` (bot — экспорт из `app.py`).
- Отправляет ссылку (Яндекс.Диск и т.п.) **только** тем, у кого статус `present` в `attendance`.
