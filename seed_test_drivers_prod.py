import asyncio
import os
import asyncpg
import bcrypt

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mezhgorod"
).replace("postgresql+asyncpg://", "postgresql://")

DRIVERS = [
    {
        "name": "Алибек Водитель",
        "phone": "+77001112233",
        "password": "driver123",
        "car_brand": "Toyota",
        "car_model": "Camry",
        "car_year": 2018,
        "car_color": "Белый",
        "car_number": "123ABC01",
    },
    {
        "name": "Ержан Жолаушы",
        "phone": "+77001112244",
        "password": "driver123",
        "car_brand": "Hyundai",
        "car_model": "Sonata",
        "car_year": 2020,
        "car_color": "Чёрный",
        "car_number": "456XYZ01",
    },
]


async def main():
    conn = await asyncpg.connect(DATABASE_URL)

    for d in DRIVERS:
        hashed = bcrypt.hashpw(d["password"].encode(), bcrypt.gensalt()).decode()

        user_id = await conn.fetchval(
            """
            INSERT INTO users (name, phone, password_hash, role)
            VALUES ($1, $2, $3, 'driver')
            ON CONFLICT (phone) DO UPDATE SET role = 'driver', name = EXCLUDED.name
            RETURNING id
            """,
            d["name"], d["phone"], hashed,
        )

        existing_profile = await conn.fetchrow(
            "SELECT id FROM driver_profiles WHERE user_id = $1", user_id
        )
        if existing_profile:
            print(f"  Профиль уже есть: {d['name']}")
            continue

        await conn.execute(
            """
            INSERT INTO driver_profiles
                (user_id, car_brand, car_model, car_year, car_color, car_number, is_verified, rating, balance)
            VALUES ($1, $2, $3, $4, $5, $6, true, 5.0, 500)
            """,
            user_id, d["car_brand"], d["car_model"], d["car_year"], d["car_color"], d["car_number"],
        )
        print(f"  Создан водитель: {d['name']} / {d['phone']} / пароль: {d['password']}")

    await conn.close()
    print("\nГотово.")


asyncio.run(main())
