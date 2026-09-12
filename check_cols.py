import sqlite3
conn = sqlite3.connect('data/portfolio.db')
c = conn.cursor()
c.execute("PRAGMA table_info(trades)")
print([row[1] for row in c.fetchall()])
