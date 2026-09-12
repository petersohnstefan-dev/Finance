import codecs

with codecs.open('src/db.py', 'r', 'utf8') as f:
    content = f.read()

# Fix signature
old_sig = '''    def record_trade(self, depot_id: str, trade_type: str, symbol: str, name: str, 
                     shares: float, total_amount: float, price: float, 
                     sell_price: Optional[float] = None, pnl: Optional[float] = None, 
                     pnl_pct: Optional[float] = None, reason: str = "",
                     executed_at: Optional[str] = None):'''

new_sig = '''    def record_trade(self, depot_id: str, trade_type: str, symbol: str, name: str, 
                     shares: float, total_amount: float, price: float, 
                     sell_price: Optional[float] = None, pnl: Optional[float] = None, 
                     pnl_pct: Optional[float] = None, reason: str = "",
                     executed_at: Optional[str] = None, fees: float = 0.0):'''
content = content.replace(old_sig, new_sig)

# Fix INSERT statement
old_insert = '''            INSERT INTO trades (
                depot_id, trade_type, symbol, name, shares, buy_price, sell_price, 
                total_amount, pnl, pnl_pct, executed_at, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                depot_id, trade_type, symbol, name, shares, 
                buy_p, sell_p,
                total_amount, pnl, pnl_pct, now_str, reason
            ))'''

new_insert = '''            INSERT INTO trades (
                depot_id, trade_type, symbol, name, shares, buy_price, sell_price, 
                total_amount, pnl, pnl_pct, executed_at, reason, fees
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                depot_id, trade_type, symbol, name, shares, 
                buy_p, sell_p,
                total_amount, pnl, pnl_pct, now_str, reason, fees
            ))'''
content = content.replace(old_insert, new_insert)

with codecs.open('src/db.py', 'w', 'utf8') as f:
    f.write(content)
print("DB patched!")
