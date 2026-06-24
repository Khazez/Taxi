"""Добавляет адрес назначения и дополнительные адреса в trip_requests и bookings."""
import psycopg2

conn = psycopg2.connect(
    dbname="mezhgorod", user="postgres", password="postgres",
    host="localhost", port=5432,
)
cur = conn.cursor()

changes = [
    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS destination_address VARCHAR",
    "ALTER TABLE trip_requests ADD COLUMN IF NOT EXISTS extra_pickups TEXT",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS destination_address VARCHAR",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS extra_pickups TEXT",
]

for sql in changes:
    print(f"  {sql[:70]}...")
    cur.execute(sql)

conn.commit()
cur.close()
conn.close()
print("Готово!")
