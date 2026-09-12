import codecs
import re

with codecs.open('src/portfolio.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix buy method logging
old_db_buy = 'self.db.record_trade(depot_key, "BUY", symbol, name, shares, cost, price, reason=reason)'
new_db_buy = 'fee = cost * SPREAD_PCT + 1.00; self.db.record_trade(depot_key, "BUY", symbol, name, shares, cost, price, reason=reason, fees=fee)'
content = content.replace(old_db_buy, new_db_buy)

# Fix sell method logging
old_db_sell = 'self.db.record_trade(depot_key, "SELL", symbol, pos["name"], shares, revenue, \n                                 pos["buy_price"], sell_price=price, pnl=pnl, pnl_pct=pnl_pct, reason=reason)'
new_db_sell = 'fee = (shares * price) * SPREAD_PCT + 1.00; self.db.record_trade(depot_key, "SELL", symbol, pos["name"], shares, revenue, \n                                 pos["buy_price"], sell_price=price, pnl=pnl, pnl_pct=pnl_pct, reason=reason, fees=fee)'
content = content.replace(old_db_sell, new_db_sell)

old_db_sell_2 = 'self.db.record_trade(depot_key, "SELL", symbol, pos["name"], shares, revenue, pos["buy_price"], sell_price=price, pnl=pnl, pnl_pct=pnl_pct, reason=reason)'
new_db_sell_2 = 'fee = (shares * price) * SPREAD_PCT + 1.00; self.db.record_trade(depot_key, "SELL", symbol, pos["name"], shares, revenue, pos["buy_price"], sell_price=price, pnl=pnl, pnl_pct=pnl_pct, reason=reason, fees=fee)'
content = content.replace(old_db_sell_2, new_db_sell_2)

# Deduct fee from cash
old_cash_buy = 'depot["cash"] -= cost'
new_cash_buy = 'depot["cash"] -= (cost + 1.00)'
content = content.replace(old_cash_buy, new_cash_buy)

old_cash_sell = 'depot["cash"] += revenue'
new_cash_sell = 'depot["cash"] += (revenue - 1.00)'
content = content.replace(old_cash_sell, new_cash_sell)

with codecs.open('src/portfolio.py', 'w', 'utf-8') as f:
    f.write(content)

print("Patched portfolio.py with fees.")
