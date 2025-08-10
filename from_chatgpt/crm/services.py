# 📁 from_chatgpt/crm/services.py
# Модуль для взаимодействия с БД CRM.
# Пароли ХРАНЯТСЯ ТОЛЬКО В ВИДЕ bcrypt-хэша (со встроенной солью).

from datetime import datetime
import aiosqlite
import bcrypt

from .models import DB_PATH


def _hash(password: str) -> str:
    """Вернёт bcrypt-хэш пароля (со встроенной солью)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ───────────────────────────── Пользователи ─────────────────────────────

async def add_user(
    telegram_id: int,
    full_name: str,
    nickname: str,
    role: str = "participant",
    phone: str = "",
    email: str = "",
    password: str = "",
):
    """Создать пользователя или обновить его данные по telegram_id.
    Пароль, если передан, будет сохранён как bcrypt-хэш.
    """
    pwd_to_store = _hash(password) if password else ""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (telegram_id, full_name, nickname, role, phone, email, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                full_name = excluded.full_name,
                nickname  = excluded.nickname,
                role      = excluded.role,
                phone     = excluded.phone,
                email     = excluded.email,
                password  = CASE
                                WHEN excluded.password <> '' THEN excluded.password
                                ELSE users.password
                            END
            """,
            (telegram_id, full_name, nickname, role, phone, email, pwd_to_store),
        )
        await db.commit()


async def get_user_by_telegram(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            return await cursor.fetchone()


async def get_user_by_nickname(nickname: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE nickname = ?", (nickname,)) as cursor:
            return await cursor.fetchone()


async def update_user_password(nickname: str, new_password: str):
    """Обновить пароль (с хэшированием)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET password = ? WHERE nickname = ?",
            (_hash(new_password), nickname),
        )
        await db.commit()


async def verify_user_password(nickname: str, password_plain: str) -> bool:
    """Проверить пароль: сравнить введённый с хранящимся хэшем.
    Мягкая миграция: если в БД лежит старый «голый» пароль и он совпал,
    сразу перехэшируем и сохраним.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT password FROM users WHERE nickname = ?", (nickname,)) as cursor:
            row = await cursor.fetchone()

    if not row:
        return False

    stored = row[0] or ""

    # Если по историческим причинам в БД лежит «plain»
    if stored and not stored.startswith("$2"):
        if stored == password_plain:
            # Перехэшируем и сохраняем
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE users SET password = ? WHERE nickname = ?",
                    (_hash(password_plain), nickname),
                )
                await db.commit()
            return True
        return False

    # Обычная проверка bcrypt
    if not stored:
        return False
    try:
        return bcrypt.checkpw(password_plain.encode("utf-8"), stored.encode("utf-8"))
    except Exception:
        return False


async def update_user_role(user_id: int, new_role: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET role = ? WHERE telegram_id = ?",
            (new_role, user_id),
        )
        await db.commit()


# ───────────────────────────── Потоки/участники ─────────────────────────────

async def get_streams():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, name, start_date, end_date, status FROM streams"
        ) as cursor:
            return await cursor.fetchall()


async def get_participants_by_stream(stream_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT u.full_name, p.status, p.registered_at
            FROM participants p
            JOIN users u ON u.id = p.user_id
            WHERE p.stream_id = ?
            """,
            (stream_id,),
        ) as cursor:
            return await cursor.fetchall()


async def register_participant(telegram_id: int, stream_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # Получим id пользователя по telegram_id
        async with db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            user_id = row[0]

        # Проверим, не зарегистрирован ли уже
        async with db.execute(
            "SELECT id FROM participants WHERE user_id = ? AND stream_id = ?",
            (user_id, stream_id),
        ) as cursor:
            exists = await cursor.fetchone()
            if exists:
                return False

        await db.execute(
            "INSERT INTO participants (user_id, stream_id, registered_at) VALUES (?, ?, ?)",
            (user_id, stream_id, datetime.now().isoformat()),
        )
        await db.commit()
        return True


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
                ("Новый поток (январь 2026)", "2026-01-01", "2026-04-01", "planned"),
            ],
        )
        await db.commit()


# ───────────────────────────── Прочее ─────────────────────────────

async def clear_user_password_by_telegram(telegram_id: int):
    """Очистка пароля по Telegram ID (выход без удаления пользователя)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET password = '' WHERE telegram_id = ?",
            (telegram_id,),
        )
        await db.commit()
