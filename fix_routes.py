"""
Добавляет обратные маршруты для всех существующих односторонних маршрутов.
Запуск: python fix_routes.py
"""
import psycopg2

conn = psycopg2.connect(
    dbname="mezhgorod",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432
)
cur = conn.cursor()

# Получаем все маршруты с ценами
cur.execute("""
    SELECT r.id, r.city_from, r.city_to, rp.price
    FROM routes r
    LEFT JOIN LATERAL (
        SELECT price FROM route_prices WHERE route_id = r.id ORDER BY created_at DESC LIMIT 1
    ) rp ON true
    WHERE r.is_active = 1
""")
routes = cur.fetchall()

added = 0
for route_id, city_from, city_to, price in routes:
    # Проверяем есть ли уже обратный маршрут
    cur.execute(
        "SELECT id FROM routes WHERE city_from = %s AND city_to = %s AND is_active = 1",
        (city_to, city_from)
    )
    if cur.fetchone():
        print(f"  Уже есть: {city_to} → {city_from}")
        continue

    # Создаём обратный маршрут
    cur.execute(
        "INSERT INTO routes (city_from, city_to, is_active) VALUES (%s, %s, 1) RETURNING id",
        (city_to, city_from)
    )
    new_id = cur.fetchone()[0]

    # Добавляем цену (такую же)
    if price:
        cur.execute(
            "INSERT INTO route_prices (route_id, price) VALUES (%s, %s)",
            (new_id, price)
        )

    print(f"  Добавлен: {city_to} → {city_from} (цена: {price})")
    added += 1

conn.commit()
cur.close()
conn.close()
print(f"\nГотово. Добавлено обратных маршрутов: {added}")
