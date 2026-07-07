import asyncio
import os
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mezhgorod"
).replace("postgresql+asyncpg://", "postgresql://")

CITY = "Актобе"
ROUTES = [
    ("Хромтау", 2500),
    ("Кандыагаш", 2000),
    ("Алга", 800),
    ("Кобда", 2000),
    ("Мартук", 1500),
    ("Шубаркудык", 2500),
    ("Батамша", 2000),
    ("Карауылкелды", 3000),
    ("Айтекеби", 5000),
    ("Шалкар", 10000),
]


async def main():
    conn = await asyncpg.connect(DATABASE_URL)

    added = 0
    for city, price in ROUTES:
        for city_from, city_to in [(CITY, city), (city, CITY)]:
            existing = await conn.fetchrow(
                "SELECT id FROM routes WHERE city_from = $1 AND city_to = $2 AND is_active = 1",
                city_from, city_to,
            )
            if existing:
                print(f"  Уже есть: {city_from} → {city_to}")
                continue

            route_id = await conn.fetchval(
                "INSERT INTO routes (city_from, city_to, is_active) VALUES ($1, $2, 1) RETURNING id",
                city_from, city_to,
            )
            await conn.execute(
                "INSERT INTO route_prices (route_id, price) VALUES ($1, $2)",
                route_id, price,
            )
            print(f"  Добавлен: {city_from} → {city_to} ({price}₸)")
            added += 1

    print(f"\nГотово. Добавлено маршрутов: {added}")
    await conn.close()


asyncio.run(main())
