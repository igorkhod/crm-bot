from __future__ import annotations
from crm2.db.core import get_db_connection

def ensure_admin_schema() -> None:
    with get_db_connection() as con:
        cur = con.cursor()
        # Материалы (файлы можно хранить как telegram file_id)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS materials (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          body  TEXT,
          tg_file_id TEXT,        -- document/photo/audio/video as file_id
          mime TEXT,
          created_by INTEGER,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # Домашние задания (можно привязывать к материалу)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          body  TEXT,
          material_id INTEGER,
          due_date TEXT,          -- ISO (YYYY-MM-DD)
          created_by INTEGER,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # Рассылки
        cur.execute("""
        CREATE TABLE IF NOT EXISTS broadcasts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          body  TEXT,
          attachment_file_id TEXT,
          attachment_mime TEXT,
          audience TEXT NOT NULL,     -- 'all' | 'cohort'
          cohort_id INTEGER,          -- если audience='cohort'
          created_by INTEGER,
          scheduled_at TEXT,          -- NULL => сразу
          sent_at TEXT,
          status TEXT DEFAULT 'pending',  -- pending|sending|done|error
          stats_json TEXT
        );
        """)
        # Получатели и статусы доставки
        cur.execute("""
        CREATE TABLE IF NOT EXISTS broadcast_recipients (
          broadcast_id INTEGER NOT NULL,
          user_id INTEGER NOT NULL,
          status TEXT DEFAULT 'queued',  -- queued|sent|failed
          error TEXT,
          sent_at TEXT,
          PRIMARY KEY (broadcast_id, user_id)
        );
        """)
        con.commit()
