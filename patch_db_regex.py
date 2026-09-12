import re

with open('src/db.py', 'r', encoding='utf-8') as f:
    c = f.read()

replacement = '''INSERT INTO trades (
                depot_id, trade_type, symbol, name, shares, buy_price, sell_price, 
                total_amount, pnl, pnl_pct, executed_at, reason, fees
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                depot_id, trade_type, symbol, name, shares, 
                buy_p, sell_p,
                total_amount, pnl, pnl_pct, now_str, reason, fees
            ))
            conn.commit()'''

c = re.sub(r'INSERT INTO trades \([\s\S]*?conn\.commit\(\)', replacement, c)

with open('src/db.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("regex patched")
