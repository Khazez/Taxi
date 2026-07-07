"""Создаёт тестового водителя для разработки."""
import psycopg2
import bcrypt

conn = psycopg2.connect(
    dbname="mezhgorod",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432,
)
cur = conn.cursor()

phone = "+77001112233"
password = "driver123"
name = "Алибек Водитель"

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

cur.execute(
    """
    INSERT INTO users (name, phone, password_hash, role)
    VALUES (%s, %s, %s, 'driver')
    ON CONFLICT (phone) DO UPDATE SET role = 'driver', name = EXCLUDED.name
    RETURNING id, name, phone, role
    """,
    (name, phone, hashed),
)
row = cur.fetchone()
conn.commit()
cur.close()
conn.close()

print(f"Водитель создан:")
print(f"  ID:     {row[0]}")
print(f"  Имя:    {row[1]}")
print(f"  Телефон:{row[2]}")
print(f"  Роль:   {row[3]}")
print(f"  Пароль: {password}")
