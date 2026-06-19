import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/mezhgorod")
    rows = await conn.fetch("SELECT id, name, email, role FROM users WHERE role = 'admin'")
    for r in rows:
        print(r)
    await conn.close()

asyncio.run(main())