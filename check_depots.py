import sqlite3
db_path = "data/portfolio.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT id, name FROM portfolios")
for r in cur.fetchall(): print(r)
conn.close()
