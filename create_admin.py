import asyncio
import asyncpg
import bcrypt

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/mezhgorod")
    
    password = "Admin1234"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    await conn.execute(
        "UPDATE users SET password_hash = $1 WHERE email = $2",
        hashed, "admin@zholaushy.kz"
    )
    print("Пароль обновлён!")
    await conn.close()

asyncio.run(main())