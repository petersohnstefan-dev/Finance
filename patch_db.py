with open('src/db.py', 'r', encoding='utf-8') as f:
    db_content = f.read()

db_content = db_content.replace(
    'def log_trade(self, depot_id: str, trade_type: str, symbol: str, name: str, shares: float, buy_price: float, sell_price: float = 0.0, pnl: float = 0.0, pnl_pct: float = 0.0, reason: str = ""):',
    'def log_trade(self, depot_id: str, trade_type: str, symbol: str, name: str, shares: float, buy_price: float, sell_price: float = 0.0, pnl: float = 0.0, pnl_pct: float = 0.0, reason: str = "", fees: float = 0.0):'
)

db_content = db_content.replace(
    'INSERT INTO trades (depot_id, trade_type, symbol, name, shares, buy_price, sell_price, total_amount, pnl, pnl_pct, executed_at, reason)',
    'INSERT INTO trades (depot_id, trade_type, symbol, name, shares, buy_price, sell_price, total_amount, pnl, pnl_pct, executed_at, reason, fees)'
)

db_content = db_content.replace(
    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
)

db_content = db_content.replace(
    '(depot_id, trade_type, symbol, name, shares, buy_price, sell_price, total, pnl, pnl_pct, now, reason)',
    '(depot_id, trade_type, symbol, name, shares, buy_price, sell_price, total, pnl, pnl_pct, now, reason, fees)'
)

with open('src/db.py', 'w', encoding='utf-8') as f:
    f.write(db_content)

print('Patched src/db.py')
