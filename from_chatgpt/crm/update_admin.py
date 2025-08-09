import asyncio
import aiosqlite # 📦 Импорт модуля



# Путь к базе
db_path = "crm.db"

# Ваш telegram_id
your_id = 448124106  # замени при необходимости

async def main():
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            "UPDATE users SET role = 'admin' WHERE telegram_id = ?",
            (your_id,)
        )
        await conn.commit()
        print("✅ Роль успешно обновлена.")

if __name__ == "__main__":
    asyncio.run(main())
