import os
import re

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update buy signature
content = content.replace(
    'def buy(self, depot_key: str, symbol: str, name: str, shares: float, price: float, \n        reason: str = "", stop_loss: float = None, take_profit: float = None, derivative_meta=None) -> bool:',
    'def buy(self, depot_key: str, symbol: str, name: str, shares: float, price: float, \n        reason: str = "", stop_loss: float = None, take_profit: float = None, derivative_meta=None, fee: float = 1.00) -> bool:'
)

content = content.replace(
    'def buy(self, depot_key: str, symbol: str, name: str, shares: float, price: float, reason: str = "", stop_loss: float = None, take_profit: float = None, derivative_meta=None) -> bool:',
    'def buy(self, depot_key: str, symbol: str, name: str, shares: float, price: float, reason: str = "", stop_loss: float = None, take_profit: float = None, derivative_meta=None, fee: float = 1.00) -> bool:'
)

# 2. Buy logic - find the block and replace
buy_block = """        total_cost = shares * price
        
        # Add simulated 0.1% slippage for realism
        slippage = total_cost * 0.001
        effective_price = price + (price * 0.001)
        total_cost = shares * effective_price"""

new_buy_block = """        # Add simulated 0.1% slippage for realism + 1.00 Broker Fee
        slippage = (shares * price) * 0.001
        effective_price = price + (price * 0.001)
        total_cost = (shares * effective_price) + fee"""

if buy_block in content:
    content = content.replace(buy_block, new_buy_block)

# 3. Sell signature
content = content.replace(
    'def sell(self, depot_key: str, symbol: str, price: float, reason: str = "", shares_to_sell: Optional[float] = None) -> bool:',
    'def sell(self, depot_key: str, symbol: str, price: float, reason: str = "", shares_to_sell: Optional[float] = None, fee: float = 1.00) -> bool:'
)

# 4. Sell logic
sell_block = """        # Subtract 0.1% slippage
        effective_price = price - (price * 0.001)
        total_revenue = shares * effective_price"""

new_sell_block = """        # Subtract 0.1% slippage + 1.00 Broker Fee
        effective_price = price - (price * 0.001)
        total_revenue = (shares * effective_price) - fee"""

if sell_block in content:
    content = content.replace(sell_block, new_sell_block)

# 5. DB log_trade replace
content = content.replace(
    'self.db.log_trade(depot_key, "SELL", symbol, pos["name"], shares, \n                                 pos["buy_price"], sell_price=price, pnl=pnl, pnl_pct=pnl_pct, reason=reason)',
    'self.db.log_trade(depot_key, "SELL", symbol, pos["name"], shares, \n                                 pos["buy_price"], sell_price=price, pnl=pnl, pnl_pct=pnl_pct, reason=reason, fees=fee)'
)
content = content.replace(
    'self.db.log_trade(depot_key, "SELL", symbol, pos["name"], shares, pos["buy_price"], sell_price=price, pnl=pnl, pnl_pct=pnl_pct, reason=reason)',
    'self.db.log_trade(depot_key, "SELL", symbol, pos["name"], shares, pos["buy_price"], sell_price=price, pnl=pnl, pnl_pct=pnl_pct, reason=reason, fees=fee)'
)

content = content.replace(
    'self.db.log_trade(depot_key, "BUY", symbol, name, shares, effective_price, reason=reason)',
    'self.db.log_trade(depot_key, "BUY", symbol, name, shares, effective_price, reason=reason, fees=fee)'
)

with open('src/portfolio.py', 'w', encoding='utf-8') as f:
    f.write(content)

# We also need to update data_db.py to accept `fees` in `log_trade`
with open('src/data_db.py', 'r', encoding='utf-8') as f:
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

with open('src/data_db.py', 'w', encoding='utf-8') as f:
    f.write(db_content)

print("Patched portfolio.py and data_db.py")
