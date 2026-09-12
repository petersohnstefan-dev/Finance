import sqlite3
db_path = "data/portfolio.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='trades'")
print(cur.fetchone()[0])
conn.close()
