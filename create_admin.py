import asyncio
import os
import asyncpg
import bcrypt

EMAIL    = "admin@zholaushy.kz"
PASSWORD = "Admin1234"
NAME     = "Admin"
PHONE    = "+70000000000"

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mezhgorod"
).replace("postgresql+asyncpg://", "postgresql://")

async def main():
    conn = await asyncpg.connect(DATABASE_URL)

    hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()

    existing = await conn.fetchrow("SELECT id, role FROM users WHERE email = $1", EMAIL)

    if existing:
        await conn.execute(
            "UPDATE users SET password_hash = $1, role = 'admin' WHERE email = $2",
            hashed, EMAIL
        )
        print(f"✅ Обновлён: {EMAIL}")
    else:
        await conn.execute(
            "INSERT INTO users (name, phone, email, password_hash, role) VALUES ($1, $2, $3, $4, 'admin')",
            NAME, PHONE, EMAIL, hashed
        )
        print(f"✅ Создан: {EMAIL}")

    print(f"   Пароль: {PASSWORD}")
    await conn.close()

asyncio.run(main())
