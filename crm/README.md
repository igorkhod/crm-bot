# Psytech Bot (aiogram 3.x)

## 📌 Описание
Телеграм‑бот для управления обучающими потоками ("Психонетика").
Функции:
- регистрация и вход по никнейму/паролю;
- учёт ролей (user/admin);
- расписание занятий;
- уведомления администратору при запуске/остановке;
- управление пользователями и потоками.

---

## 🚀 Деплой

### Render
1. Подключить GitHub‑репозиторий.
2. Указать start‑command:
   ```bash
   python -m crm2
   ```
3. Добавить переменные окружения (TELEGRAM_TOKEN, DB_PATH и т.п.).

### VPS (Ubuntu 22.04, systemd)
1. Установить зависимости:
   ```bash
   sudo apt update && sudo apt install python3-venv sqlite3
   ```
2. Склонировать репозиторий в `/opt/psytech-bot`.
3. Создать виртуальное окружение:
   ```bash
   python3 -m venv /opt/psytech-bot/venv
   /opt/psytech-bot/venv/bin/pip install -r requirements.txt
   ```
4. Создать файл окружения `/etc/psytech-bot.env`:
   ```ini
   ENV_LABEL=prod
   TELEGRAM_TOKEN=...
   DB_PATH=/var/data/crm.db
   LOG_LEVEL=INFO
   ADMIN_ID=448124106
   ```
5. Настроить systemd:
   ```ini
   [Unit]
   Description=Psytech Telegram Bot (aiogram)
   After=network.target

   [Service]
   Type=simple
   User=botuser
   WorkingDirectory=/opt/psytech-bot/app
   EnvironmentFile=/etc/psytech-bot.env
   ExecStart=/opt/psytech-bot/venv/bin/python -m crm2
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable psytech-bot
   sudo systemctl start psytech-bot
   ```

---

## 🔔 Уведомления
- `🚀 Бот запущен!` при старте systemd.
- `⛔ Бот остановлен.` при остановке.

---

## 📂 Документация
Подробная структура: [crm2/PROJECT_MAP.full.md](crm2/PROJECT_MAP.full.md)
