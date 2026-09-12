import sqlite3
c = sqlite3.connect('data/portfolio.db')
c.execute("INSERT OR IGNORE INTO daily_snapshots (snapshot_date, depot_id, total_value, cash, invested_value, pnl, pnl_pct, num_positions) VALUES ('2026-08-26', 'day_trading', 10000.0, 10000.0, 0.0, 0.0, 0.0, 0)")
c.commit()
print('Daily backfilled.')
