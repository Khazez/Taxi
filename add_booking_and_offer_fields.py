"""Добавляет поля адреса в bookings и цену/необязательный trip_id в trip_offers."""
import psycopg2

conn = psycopg2.connect(
    dbname="mezhgorod", user="postgres", password="postgres",
    host="localhost", port=5432,
)
cur = conn.cursor()

changes = [
    # bookings — поля адреса пассажира
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS pickup_address VARCHAR",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS entrance VARCHAR",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS contact_name VARCHAR",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS contact_phone VARCHAR",
    # trip_offers — цена и необязательный trip
    "ALTER TABLE trip_offers ADD COLUMN IF NOT EXISTS price_per_seat NUMERIC(10,2)",
    "ALTER TABLE trip_offers ALTER COLUMN trip_id DROP NOT NULL",
]

for sql in changes:
    print(f"  {sql[:60]}...")
    cur.execute(sql)

conn.commit()
cur.close()
conn.close()
print("Готово!")
