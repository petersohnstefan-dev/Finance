import json
import sqlite3
from src.db import PortfolioDB

db = PortfolioDB()

with open('data/portfolios.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for depot_key, depot in data['portfolios'].items():
    history = depot.get('history', [])
    for t in history:
        # Check if trade exists
        with db._get_conn() as conn:
            cur = conn.cursor()
            date_val = t.get('executed_at') or t.get('date')
            cur.execute("""
                SELECT id FROM trades 
                WHERE depot_id = ? AND symbol = ? AND executed_at = ? AND trade_type = ?
            """, (depot_key, t['symbol'], date_val, t['type']))
            if cur.fetchone() is None:
                # Insert it using keyword arguments to avoid mistakes!
                print(f"Backfilling {t['type']} {t['symbol']} at {date_val}")
                
                price = t.get('buy_price', 0) if t['type'] == 'BUY' else t.get('sell_price', 0)
                
                db.record_trade(
                    depot_id=depot_key,
                    trade_type=t['type'],
                    symbol=t['symbol'],
                    name=t.get('name', t['symbol']),
                    shares=t.get('shares', 0),
                    total_amount=t.get('total', 0),
                    price=price,
                    sell_price=t.get('sell_price') if t['type'] == 'SELL' else None,
                    pnl=t.get('pnl'),
                    pnl_pct=t.get('pnl_pct'),
                    reason=t.get('reason', ''),
                    executed_at=date_val
                )
print("Backfill complete")
