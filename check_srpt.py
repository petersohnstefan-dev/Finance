import sqlite3
import pandas as pd
conn = sqlite3.connect('data/portfolio.db')
cursor = conn.cursor()
cursor.execute("SELECT trade_type, symbol, executed_at, reason FROM trades WHERE symbol='SRPT' OR symbol='NVAX'")
cols = [description[0] for description in cursor.description]
df = pd.DataFrame(cursor.fetchall(), columns=cols)
df.to_csv('scratch_srpt.csv', index=False, encoding='utf-8')
