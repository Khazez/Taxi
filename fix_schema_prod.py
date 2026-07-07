import asyncio
import os
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mezhgorod"
).replace("postgresql+asyncpg://", "postgresql://")

CREATE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS platform_settings (
        id SERIAL PRIMARY KEY,
        key VARCHAR UNIQUE NOT NULL,
        value VARCHAR NOT NULL,
        description VARCHAR,
        updated_at TIMESTAMPTZ
    )
    """,
]

ADD_COLUMNS = [
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS is_departed BOOLEAN DEFAULT false",
    "ALTER TABLE trips ADD COLUMN IF NOT EXISTS is_arrived BOOLEAN DEFAULT false",

    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS pickup_address VARCHAR",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS entrance VARCHAR",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS extra_pickups TEXT",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS destination_address VARCHAR",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS destination_entrance VARCHAR",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS extra_destinations TEXT",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS contact_name VARCHAR",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS contact_phone VARCHAR",

    "ALTER TABLE driver_profiles ADD COLUMN IF NOT EXISTS balance NUMERIC(10,2) DEFAULT 0",

    "ALTER TABLE ratings ADD COLUMN IF NOT EXISTS comment VARCHAR",

    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS contact_name VARCHAR",
    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS contact_phone VARCHAR",
    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS pickup_address VARCHAR",
    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS entrance VARCHAR",
    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS extra_pickups TEXT",
    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS destination_address VARCHAR",
    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS destination_entrance VARCHAR",
    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS extra_destinations TEXT",
    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS payment_type VARCHAR DEFAULT 'cash'",

    "ALTER TABLE trip_offers ADD COLUMN IF NOT EXISTS price_per_seat NUMERIC(10,2)",
]


async def main():
    conn = await asyncpg.connect(DATABASE_URL)

    for stmt in CREATE_TABLES:
        await conn.execute(stmt)
        print(f"OK (table): {stmt.strip().splitlines()[1].strip()}")

    for stmt in ADD_COLUMNS:
        await conn.execute(stmt)
        print(f"OK: {stmt}")

    await conn.close()
    print("\nГотово. Схема прод-БД синхронизирована с моделями.")


asyncio.run(main())
