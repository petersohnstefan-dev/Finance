import sqlite3
c = sqlite3.connect('data/portfolio.db')
cursor = c.cursor()
cursor.execute("SELECT snapshot_time FROM hourly_snapshots WHERE depot_id='short_term'")
times = [r[0] for r in cursor.fetchall()]
for t in times:
    cursor.execute("""
        INSERT OR IGNORE INTO hourly_snapshots (snapshot_time, depot_id, total_value, cash, invested_value, pnl, pnl_pct, num_positions)
        VALUES (?, 'day_trading', 10000.0, 10000.0, 0.0, 0.0, 0.0, 0)
    """, (t,))
c.commit()
print('Daytrading backfilled.')
