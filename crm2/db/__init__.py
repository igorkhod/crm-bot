# === Автогенерированный заголовок: crm2/db/__init__.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: get_upcoming_sessions, get_session_by_id
# Переменные: db
# === Конец автозаголовка


# crm2/db/__init__.py
from .core import get_db_connection
from .sessions import get_upcoming_sessions, get_session_by_id

# Создаём ленивое подключение (каждый раз новый connection)
# или можешь сделать пул, если нужно
class Database:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    async def execute(self, sql: str, params: tuple = ()):
        con = self._get_connection()
        cur = con.cursor()
        cur.execute(sql, params)
        con.commit()
        cur.close()
        con.close()

    async def fetch_all(self, sql: str, params: tuple = ()):
        con = self._get_connection()
        cur = con.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        con.close()
        return rows

    async def fetch_one(self, sql: str, params: tuple = ()):
        con = self._get_connection()
        cur = con.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        con.close()
        return row

# Вот теперь у тебя есть db
db = Database(get_db_connection)

__all__ = [
    "db",
    "get_upcoming_sessions",
    "get_session_by_id",
]
