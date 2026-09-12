import codecs

with codecs.open('src/db.py', 'r', 'utf8') as f:
    content = f.read()

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

with codecs.open('src/db.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched signature")
