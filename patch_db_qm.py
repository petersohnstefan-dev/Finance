import codecs

with codecs.open('src/db.py', 'r', 'utf8') as f:
    content = f.read()

old_insert = '''            INSERT INTO trades (
                depot_id, trade_type, symbol, name, shares, buy_price, sell_price, 
                total_amount, pnl, pnl_pct, executed_at, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

new_insert = '''            INSERT INTO trades (
                depot_id, trade_type, symbol, name, shares, buy_price, sell_price, 
                total_amount, pnl, pnl_pct, executed_at, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

content = content.replace(old_insert, new_insert)

with codecs.open('src/db.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched DB question mark")
