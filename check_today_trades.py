import sqlite3
import pandas as pd

conn = sqlite3.connect('data/portfolio.db')
query = "SELECT * FROM trades WHERE executed_at LIKE '2026-09-03%'"
df = pd.read_sql_query(query, conn)
print(f"Total trades on 2026-09-03: {len(df)}")
if len(df) > 0:
    print(df)
else:
    print("No trades found for today.")
