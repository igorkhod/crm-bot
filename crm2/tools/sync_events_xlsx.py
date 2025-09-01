# === Автогенерированный заголовок: crm2/tools/sync_events_xlsx.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: pick, to_iso, ensure_schema, sync_one_file, main
# === Конец автозаголовка
# === Файл: crm2/tools/sync_events_xlsx.py
# Аннотация: синхронизация расписаний из директории .xlsx в таблицу events_xlsx.
from __future__ import annotations
import os, sqlite3
from pathlib import Path
from typing import Optional, Iterable
import pandas as pd

DB_PATH = Path(os.getenv("DB_PATH", "crm.db"))
SCHEDULE_DIR = Path(os.getenv("SCHEDULE_DIR", "/var/data/schedules"))

# Какие имена колонок распознаём
DATE_COLS = ["date", "дата", "start_date", "начало", "start", "дата_начала"]
END_COLS  = ["end_date", "конец", "end", "дата_окончания"]
TITLE_COLS = ["title", "название", "тема", "name", "topic"]
CODE_COLS  = ["code", "topic_code", "код"]
ANN_COLS   = ["annotation", "описание", "descr", "description", "аннотация"]

def pick(df: pd.DataFrame, names: Iterable[str]) -> Optional[str]:
    low = {str(c).strip().lower(): c for c in df.columns}
    for n in names:
        if n in low: return low[n]
    return None

def to_iso(v) -> Optional[str]:
    if pd.isna(v): return None
    # excel serial
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        try: return pd.to_datetime(v, origin="1899-12-30", unit="D").strftime("%Y-%m-%d")
        except: pass
    # fast paths
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M"):
        try: return pd.to_datetime(str(v).strip(), format=fmt).strftime("%Y-%m-%d")
        except: continue
    # liberal
    try: return pd.to_datetime(str(v).strip(), dayfirst=True, errors="raise").strftime("%Y-%m-%d")
    except: return None

def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute("""
      CREATE TABLE IF NOT EXISTS events_xlsx (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_date TEXT NOT NULL,
        end_date   TEXT NOT NULL,
        title      TEXT NOT NULL,
        topic_code TEXT,
        annotation TEXT,
        source_file TEXT NOT NULL
      )
    """)
    # VIEW, из которого читает бот
    con.execute("DROP VIEW IF EXISTS events_ui")
    con.execute("""
      CREATE VIEW IF NOT EXISTS events_ui AS
      SELECT id, start_date, end_date, COALESCE(topic_code,'') AS topic_code,
             COALESCE(title,'') AS title, COALESCE(annotation,'') AS annotation
      FROM events_xlsx
      UNION ALL
      SELECT
        e.id,
        CASE
          WHEN e.date LIKE '__.__.____' THEN substr(e.date,7,4)||'-'||substr(e.date,4,2)||'-'||substr(e.date,1,2)
          WHEN e.date LIKE '__-__-____' THEN substr(e.date,7,4)||'-'||substr(e.date,4,2)||'-'||substr(e.date,1,2)
          ELSE substr(e.date,1,10)
        END AS start_date,
        CASE
          WHEN e.date LIKE '__.__.____' THEN substr(e.date,7,4)||'-'||substr(e.date,4,2)||'-'||substr(e.date,1,2)
          WHEN e.date LIKE '__-__-____' THEN substr(e.date,7,4)||'-'||substr(e.date,4,2)||'-'||substr(e.date,1,2)
          ELSE substr(e.date,1,10)
        END AS end_date,
        '' AS topic_code,
        COALESCE(e.title,'') AS title,
        '' AS annotation
      FROM events e
    """)

def sync_one_file(con: sqlite3.Connection, xlsx_path: Path) -> int:
    book = pd.read_excel(xlsx_path, sheet_name=None)
    total = 0
    cur = con.cursor()
    # чистим старые строки из этого файла, чтобы избежать дублей
    cur.execute("DELETE FROM events_xlsx WHERE source_file = ?", (str(xlsx_path.name),))
    for sheet, df in book.items():
        if df.empty: continue
        dcol = pick(df, DATE_COLS)
        tcol = pick(df, TITLE_COLS)
        ecol = pick(df, END_COLS)
        ccol = pick(df, CODE_COLS)
        acol = pick(df, ANN_COLS)
        if not dcol or not tcol:
            continue
        for _, row in df.iterrows():
            sd = to_iso(row.get(dcol))
            ed = to_iso(row.get(ecol)) if ecol else sd
            title = "" if pd.isna(row.get(tcol)) else str(row.get(tcol)).strip()
            code  = None if (ccol is None or pd.isna(row.get(ccol))) else str(row.get(ccol)).strip()
            ann   = None if (acol is None or pd.isna(row.get(acol))) else str(row.get(acol)).strip()
            if sd and ed and title:
                cur.execute(
                    "INSERT INTO events_xlsx (start_date,end_date,title,topic_code,annotation,source_file) VALUES (?,?,?,?,?,?)",
                    (sd, ed, title, code, ann, xlsx_path.name)
                )
                total += 1
    con.commit()
    return total

def main():
    if not SCHEDULE_DIR.exists():
        raise SystemExit(f"SCHEDULE_DIR not found: {SCHEDULE_DIR}")
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    ensure_schema(con)
    inserted = 0
    for x in sorted(SCHEDULE_DIR.glob("*.xlsx")):
        inserted += sync_one_file(con, x)
    con.close()
    print(f"Synced {inserted} rows from {SCHEDULE_DIR}")

if __name__ == "__main__":
    main()
