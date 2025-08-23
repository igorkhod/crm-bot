# Отчёт по исходникам и структуре модулей

## Обнаруженные Python-пакеты (директории с `__init__.py`)
- `crm2`
- `crm2/db`
- `crm2/keyboards`
- `crm2/routers`

## Обнаруженные модули (.py)
- `crm2/__init__.py`
- `crm2/__main__.py`
- `crm2/app.py`
- `crm2/config.py`
- `crm2/db/__init__.py`
- `crm2/db/core.py`
- `crm2/db/sessions.py`
- `crm2/db/sqlite.py`
- `crm2/handlers/auth.py`
- `crm2/handlers/info.py`
- `crm2/handlers/registration.py`
- `crm2/handlers_schedule.py`
- `crm2/keyboards.py`
- `crm2/keyboards/__init__.py`
- `crm2/keyboards/main_menu.py`
- `crm2/keyboards/schedule.py`
- `crm2/logging_config.py`
- `crm2/routers/__init__.py`
- `crm2/routers/start.py`
- `crm2/services/schedule.py`
- `crm2/services/services.py`
- `crm2/services/users.py`
- `crm2/states.py`
- `crm2/tools/sync_events_xlsx.py`

## Модули с блоком запуска (`if __name__ == "__main__"`)
- `crm2/__main__.py`
- `crm2/tools/sync_events_xlsx.py`

## Вероятные точки входа
- `crm2/__main__.py`
- `crm2/app.py`
- `crm2/tools/sync_events_xlsx.py`

## Директории с .py без `__init__.py` (возможные проблемы импорта)
- `crm2/handlers`
- `crm2/services`
- `crm2/tools`
