import sqlite3
import sys

# Ensure stdout supports utf-8
sys.stdout.reconfigure(encoding='utf-8')

db_path = "data/portfolio.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT id, name FROM depots")
for r in cur.fetchall(): print(r)
conn.close()
