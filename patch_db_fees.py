import codecs
import re

with codecs.open('src/db.py', 'r', 'utf8') as f:
    content = f.read()

old_func = '''    def record_trade(self, depot_id: str, trade_type: str, symbol: str, name: str,
                     shares: float, total_amount: float, price: float, 
                     sell_price: Optional[float] = None, pnl: Optional[float] = None, 
                     pnl_pct: Optional[float] = None, reason: str = "",
                     executed_at: Optional[str] = None):'''

new_func = '''    def record_trade(self, depot_id: str, trade_type: str, symbol: str, name: str,
                     shares: float, total_amount: float, price: float, 
                     sell_price: Optional[float] = None, pnl: Optional[float] = None, 
                     pnl_pct: Optional[float] = None, reason: str = "",
                     executed_at: Optional[str] = None, fees: float = 0.0):'''

content = content.replace(old_func, new_func)

# And inside the function, we need to update the insert query!
# Let's find the INSERT statement
old_insert = '''            self.cursor.execute("""
                INSERT INTO trades 
                (depot_id, trade_type, symbol, name, shares, buy_price, sell_price, total_amount, pnl, pnl_pct, executed_at, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (depot_id, trade_type, symbol, name, shares, 
                  price if trade_type == "BUY" else None, 
                  sell_price, total_amount, pnl, pnl_pct, executed_at, reason))'''

new_insert = '''            self.cursor.execute("""
                INSERT INTO trades 
                (depot_id, trade_type, symbol, name, shares, buy_price, sell_price, total_amount, pnl, pnl_pct, executed_at, reason, fees)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (depot_id, trade_type, symbol, name, shares, 
                  price if trade_type == "BUY" else None, 
                  sell_price, total_amount, pnl, pnl_pct, executed_at, reason, fees))'''

content = content.replace(old_insert, new_insert)

with codecs.open('src/db.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched src/db.py")
