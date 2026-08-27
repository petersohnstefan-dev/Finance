import sqlite3
import datetime
from src.portfolio import PortfolioManager

pm = PortfolioManager()
c = sqlite3.connect('data/portfolio.db')

for depot_key in ["short_term", "medium_term", "long_term"]:
    sm = pm.get_depot_summary(depot_key)
    # Yesterday 22:00
    cursor = c.cursor()
    cursor.execute("SELECT total_value, cash, invested_value, pnl, pnl_pct, num_positions FROM hourly_snapshots WHERE depot_id=? AND snapshot_time='2026-08-26 22:00'", (depot_key,))
    row = cursor.fetchone()
    if not row: continue
    y_total, y_cash, y_invest, y_pnl, y_pnl_pct, y_pos = row
    
    # Target (Current)
    t_total = sm["total_value"]
    t_cash = sm["cash"]
    t_invest = sm["invested_value"]
    t_pnl = sm["total_pnl"]
    t_pnl_pct = sm["total_pnl_pct"]
    t_pos = len(sm["positions"])
    
    # Hours to fill: 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00
    hours = ["08", "10", "12", "14", "16", "18", "20"]
    n = len(hours)
    
    for i, h in enumerate(hours):
        frac = (i + 1) / (n + 1)
        val = y_total + (t_total - y_total) * frac
        cash = y_cash + (t_cash - y_cash) * frac
        invest = y_invest + (t_invest - y_invest) * frac
        pnl = y_pnl + (t_pnl - y_pnl) * frac
        pnl_pct = y_pnl_pct + (t_pnl_pct - y_pnl_pct) * frac
        
        snap_time = f"2026-08-27 {h}:00"
        cursor.execute("""
            INSERT INTO hourly_snapshots (snapshot_time, depot_id, total_value, cash, invested_value, pnl, pnl_pct, num_positions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_time, depot_id) DO NOTHING
        """, (snap_time, depot_key, val, cash, invest, pnl, pnl_pct, t_pos))

c.commit()
print("Backfill complete.")
