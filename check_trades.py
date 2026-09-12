import sqlite3
import json

db_path = "data/portfolio.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== TRADES ===")
cur.execute("SELECT count(*) as cnt FROM trades")
print(f"Total trades: {cur.fetchone()['cnt']}")

cur.execute("SELECT * FROM trades ORDER BY executed_at DESC LIMIT 5")
rows = [dict(r) for r in cur.fetchall()]
for r in rows:
    print(json.dumps(r, indent=2, ensure_ascii=False))

print("\n=== DEPOTS ===")
cur.execute("SELECT * FROM portfolios")
rows = [dict(r) for r in cur.fetchall()]
for r in rows:
    print(json.dumps(r, indent=2, ensure_ascii=False))

conn.close()
