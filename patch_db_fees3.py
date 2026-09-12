import codecs
import re

with codecs.open('src/db.py', 'r', 'utf8') as f:
    content = f.read()

# Replace the specific INSERT block manually using regex
pattern = r'INSERT INTO trades \([\s\S]*?conn\.commit\(\)'
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

content = re.sub(pattern, replacement, content)

with codecs.open('src/db.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched src/db.py using regex")
