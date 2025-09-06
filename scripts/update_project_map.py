#
#!/usr/bin/env python3
# C:\Users\user\PycharmProjects\crm\scripts\update_project_map.py
"""
scripts/update_project_map.py — автообновление PROJECT_MAP.full.md

Запуск: python scripts/update_project_map.py
"""

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # crm/
CRM2 = ROOT / "crm2"
MAP_FILE = CRM2 / "PROJECT_MAP.full.md"
ENV_EXAMPLE = ROOT / ".env.example"
DB_PATH = os.getenv("DB_PATH", "/var/data/crm.db")


def list_files(base: Path, exclude=("__pycache__",)):
    files = []
    for p in base.rglob("*.py"):
        if not any(ex in p.parts for ex in exclude):
            files.append(str(p.relative_to(ROOT)))
    return sorted(files)


def read_env_vars():
    if not ENV_EXAMPLE.exists():
        return []
    return [line.strip() for line in ENV_EXAMPLE.read_text().splitlines()
            if line.strip() and not line.startswith("#")]


def read_db_schema():
    if not Path(DB_PATH).exists():
        return ["(БД недоступна, используем DB_PATH=%s)" % DB_PATH]
    out = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
            for name, sql in cur.fetchall():
                out.append(f"### {name}\n```sql\n{sql}\n```")
    except Exception as e:
        out.append(f"(Ошибка чтения БД: {e})")
    return out


def build_map():
    content = ["# PROJECT_MAP.full.md — автогенерация",
               f"> Обновлено: {os.popen('date').read().strip()}",
               "",
               "## 📂 Структура файлов"]

    for section in ["handlers", "db", "services", "keyboards"]:
        files = list_files(CRM2 / section)
        if files:
            content.append(f"### {section}")
            content.extend(f"- `{f}`" for f in files)

    content.append("\n## ⚙️ Переменные окружения (.env.example)")
    content.extend(f"- `{line}`" for line in read_env_vars())

    content.append("\n## 🗄 Таблицы БД")
    content.extend(read_db_schema())

    return "\n".join(content)


def main():
    MAP_FILE.write_text(build_map(), encoding="utf-8")
    print(f"✅ PROJECT_MAP.full.md обновлён: {MAP_FILE}")


if __name__ == "__main__":
    main()
