import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/mezhgorod')
cur = conn.cursor()
cur.execute("INSERT INTO platform_settings (key, value) VALUES ('cancellation_fee_percent', '20')")
conn.commit()
conn.close()
print("Done!")