import re

with open('src/db.py', 'r', encoding='utf-8') as f:
    c = f.read()

sig_pattern = r'def record_trade\(self, depot_id: str, trade_type: str, symbol: str, name: str,[\s\S]*?executed_at: Optional\[str\] = None\):'
new_sig = '''def record_trade(self, depot_id: str, trade_type: str, symbol: str, name: str, 
                     shares: float, total_amount: float, price: float, 
                     sell_price: Optional[float] = None, pnl: Optional[float] = None, 
                     pnl_pct: Optional[float] = None, reason: str = "",
                     executed_at: Optional[str] = None, fees: float = 0.0):'''

c = re.sub(sig_pattern, new_sig, c)

with open('src/db.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("regex sig patched")
