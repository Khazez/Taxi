"""
Создаёт таблицу ratings и добавляет колонку comment если её нет.
Запуск: python create_ratings_table.py
"""
import psycopg2

conn = psycopg2.connect(
    dbname="mezhgorod", user="postgres", password="postgres",
    host="localhost", port=5432
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS ratings (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    from_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 5),
    comment VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW()
)
""")
print("Таблица ratings — OK")

cur.execute(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='ratings' AND column_name='comment'"
)
if not cur.fetchone():
    cur.execute("ALTER TABLE ratings ADD COLUMN comment VARCHAR")
    print("Добавлена колонка comment")
else:
    print("Колонка comment — уже есть")

conn.commit()
cur.close()
conn.close()
print("Готово.")
