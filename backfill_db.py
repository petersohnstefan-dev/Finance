import json
import sqlite3

def backfill():
    # Load JSON
    with open('data/portfolios.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
        
    conn = sqlite3.connect('data/portfolio.db')
    c = conn.cursor()
    
    # Get existing trades to avoid duplicates
    c.execute("SELECT depot_id, symbol, trade_type, executed_at FROM trades")
    existing = set((r[0], r[1], r[2], r[3]) for r in c.fetchall())
    
    added = 0
    for depot_key, depot_data in d['portfolios'].items():
        hist = depot_data.get('history', [])
        for t in hist:
            trade_type = t.get('action') or t.get('type')
            sym = t.get('symbol')
            ex_at = t.get('date')
            
            # Check if this exact trade is in DB
            if (depot_key, sym, trade_type, ex_at) not in existing:
                print(f"Missing trade found: {depot_key} {trade_type} {sym} at {ex_at}")
                
                c.execute("""
                    INSERT INTO trades 
                    (depot_id, trade_type, symbol, name, shares, buy_price, sell_price, total_amount, pnl, pnl_pct, executed_at, reason, fees)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    depot_key,
                    trade_type,
                    sym,
                    t.get('name', sym),
                    t.get('shares', 0),
                    t.get('price', 0) if trade_type == 'BUY' else t.get('buy_price', 0),
                    t.get('sell_price') if trade_type == 'SELL' else None,
                    t.get('total', 0),
                    t.get('pnl'),
                    t.get('pnl_pct'),
                    ex_at,
                    t.get('reason', ''),
                    t.get('fees', 0.0)
                ))
                added += 1
                
    conn.commit()
    conn.close()
    print(f"Backfilled {added} missing trades into SQLite.")

if __name__ == '__main__':
    backfill()
