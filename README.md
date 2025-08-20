# ProjectCRM

Лёгкий CRM-бот на **Aiogram 3** с локальной SQLite-базой. Этот пакет запускается командой:

```bash
python -m crm2
```

## Структура
- `crm2/` — код бота (хендлеры, сервисы, БД и т.п.)
- `requirements.txt` — зависимости
- `crm2.db` — SQLite-база (создаётся автоматически при первом запуске)

## Подготовка `.env`
Скопируйте `.env.example` → `.env` и заполните значения:

```dotenv
TELEGRAM_TOKEN=ваш_токен
ADMIN_ID=ваш_id
LOG_LEVEL=INFO
# CRM_DB=crm2.db  # можно не трогать
```

## Локальный запуск
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m crm2
```

## Развёртывание на Render (в существующий проект)
1. **GitHub.** Инициализируйте репозиторий и запушьте код:
   ```powershell
   git init
   git add .
   git commit -m "ProjectCRM: init 2025-08-20"
   git branch -M main
   git remote add origin https://github.com/ВАШ_АККАУНТ/ВАШ_РЕПО.git
   git push -u origin main
   ```
2. **Render → ваш прежний сервис (Background Worker).**
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m crm2`
   - **Auto-Deploy:** из `main`.
   - **Environment Variables:** перенесите из старого проекта или добавьте заново:
     - `TELEGRAM_TOKEN`
     - `ADMIN_ID` (опционально)
     - `LOG_LEVEL=INFO`
     - `CRM_DB=/opt/render/project/src/crm2.db` (по желанию; иначе по умолчанию)
3. **База данных.** SQLite-файл будет расположен в корне проекта (`/opt/render/project/src/crm2.db`) и создастся автоматически. Сохраните резервную копию перед миграциями.

## Альтернатива: Blueprint (опционально)
Можно создать `render.yaml` и импортировать через **Blueprints**. Пример — в этом репозитории.

## Частые вопросы
- **Как перезапустить воркер?** В Render → **Manual Deploy**.
- **Как смотреть логи?** В Render → Logs (вывод идёт через `logging`).
- **Почему бот молчит?** Проверьте токен, переменную `TELEGRAM_TOKEN`, а также что сервис — **Background Worker** (не Web Service).
