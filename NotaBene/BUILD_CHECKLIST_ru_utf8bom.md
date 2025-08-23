# Минимальный чек‑лист сборки/запуска

1. **Создать окружение Python 3.10+**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/macOS
   ```

2. **Установить зависимости**
   ```bash
   pip install -U pip
   pip install -r requirements.txt
   ```

3. **Создать .env (если требуется)** — на основе `.env.example` или описания в проекте.

4. **Проверить структуру пакетов** — директории с модулями должны содержать `__init__.py`.

5. **Запуск (варианты):**
   ```bash
   python -m crm2
   python crm2/app.py
   python crm2/tools/sync_events_xlsx.py
   ```

6. **Проверить логи и переменные окружения** — `LOG_LEVEL`, `TELEGRAM_TOKEN`, `ADMIN_ID`, `DATABASE_URL` и т.п., если используются.

7. **(Опционально) Локальная проверка БД** — если проект использует SQLite:
   ```bash
   sqlite3 crm.db '.tables'
   ```

8. **(Опционально) Запуск через модуль** — если в корне есть пакет с `__main__.py`:
   ```bash
   python -m <имя_пакета>
   ```
