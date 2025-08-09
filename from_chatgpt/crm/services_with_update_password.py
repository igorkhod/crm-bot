# 📁 from_chatgpt/crm/services.py
# services.py — модуль для взаимодействия с базой данных CRM: добавление пользователей, регистрация участников, обновление данных и получение информации о потоках и пользователях.

from .models import DB_PATH
import aiosqlite
from datetime import datetime


# Добавление нового пользователя
async def add_user(telegram_id: int, full_name: str, nickname: str, role: str = "participant", phone: str = "", email: str = "", password: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users (telegram_id, full_name, nickname, role, phone, email, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (telegram_id, full_name, nickname, role, phone, email, password)
        )
        await db.commit()


# Получить пользователя по telegram_id
async def get_user_by_telegram(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            return await cursor.fetchone()


# Получить пользователя по nickname
async def get_user_by_nickname(nickname: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE nickname = ?", (nickname,)) as cursor:
            return await cursor.fetchone()


# Обновление пароля пользователя по nickname
async def update_user_password(nickname: str, new_password: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET password = ? WHERE nickname = ?", (new_password, nickname))
        await db.commit()


# Обновление роли пользователя по telegram_id
async def update_user_role(user_id: int, new_role: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET role = ? WHERE telegram_id = ?",
            (new_role, user_id)
        )
        await db.commit()


# Получить все потоки
async def get_streams():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name, start_date, end_date, status FROM streams") as cursor:
            return await cursor.fetchall()


# Получить участников конкретного потока
async def get_participants_by_stream(stream_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT u.full_name, p.status, p.registered_at
            FROM participants p
            JOIN users u ON u.id = p.user_id
            WHERE p.stream_id = ?
        """, (stream_id,)) as cursor:
            return await cursor.fetchall()


# Регистрация пользователя на поток
async def register_participant(telegram_id: int, stream_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            user_id = row[0]

        async with db.execute("SELECT id FROM participants WHERE user_id = ? AND stream_id = ?", (user_id, stream_id)) as cursor:
            exists = await cursor.fetchone()
            if exists:
                return False

        await db.execute(
            "INSERT INTO participants (user_id, stream_id, registered_at) VALUES (?, ?, ?)",
            (user_id, stream_id, datetime.now().isoformat())
        )
        await db.commit()
        return True


# Добавление демонстрационных потоков
async def seed_demo_data():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM streams") as cursor:
            count = (await cursor.fetchone())[0]
            if count > 0:
                print("⚠️ Демонстрационные данные уже существуют, пропускаем seed.")
                return

        print("🧪 Добавляем демонстрационные потоки...")
        await db.executemany(
            "INSERT INTO streams (name, start_date, end_date, status) VALUES (?, ?, ?, ?)",
            [
                ("1-й поток (сентябрь 2023)", "2023-09-01", "2023-12-01", "finished"),
                ("2-й поток (март 2025)", "2025-03-01", "2025-06-01", "active"),
                ("Донабор (август 2025)", "2025-08-23", "2025-08-24", "active"),
                ("Новый поток (январь 2026)", "2026-01-01", "2026-04-01", "planned")
            ]
        )
        await db.commit()


# 🔄 Обновление пароля пользователя по user_id
async def update_user_password(user_id: int, new_password: str):
    # 📦 Устанавливаем соединение с базой данных SQLite по указанному пути
    async with aiosqlite.connect(DB_PATH) as db:
        # 🛠 Выполняем SQL-команду обновления пароля для нужного пользователя
        await db.execute(
            '''
            UPDATE users
            SET password = ?
            WHERE id = ?
            ''',
            (new_password, user_id)  # 📤 Передаём параметры в SQL-запрос: новый пароль и ID пользователя
        )
        # 💾 Подтверждаем изменения в базе данных
        await db.commit()
