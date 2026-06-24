"""
Добавляет новые колонки в таблицу trip_requests.
Запуск: python add_request_fields.py
"""
import psycopg2

conn = psycopg2.connect(
    dbname="mezhgorod", user="postgres", password="postgres",
    host="localhost", port=5432
)
cur = conn.cursor()

columns = [
    ("contact_name",    "VARCHAR"),
    ("contact_phone",   "VARCHAR"),
    ("pickup_address",  "VARCHAR"),
    ("entrance",        "VARCHAR"),
    ("payment_type",    "VARCHAR DEFAULT 'cash'"),
]

for col, col_type in columns:
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='trip_requests' AND column_name=%s",
        (col,)
    )
    if cur.fetchone():
        print(f"  Уже есть: {col}")
    else:
        cur.execute(f"ALTER TABLE trip_requests ADD COLUMN {col} {col_type}")
        print(f"  Добавлена: {col}")

conn.commit()
cur.close()
conn.close()
print("\nГотово.")
