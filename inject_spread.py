import sys

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update buy()
old_buy = """        depot = self.data["portfolios"].get(depot_key)
        if not depot:
            return False

        cost = shares * price
        if cost > depot["cash"]:
            shares = depot["cash"] / price
            cost = shares * price

        if shares <= 0 or cost <= 0:
            return False

        depot["cash"] -= cost
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        pos_dict = {
            "symbol": symbol,
            "name": name,
            "shares": round(shares, 4),
            "buy_price": round(price, 2),
            "current_price": round(price, 2),"""

new_buy = """        depot = self.data["portfolios"].get(depot_key)
        if not depot:
            return False

        # Apply a simulated 0.2% Bid/Ask spread penalty on buy (pay more)
        SPREAD_PCT = 0.002
        effective_price = price * (1.0 + SPREAD_PCT)

        cost = shares * effective_price
        if cost > depot["cash"]:
            shares = depot["cash"] / effective_price
            cost = shares * effective_price

        if shares <= 0 or cost <= 0:
            return False

        depot["cash"] -= cost
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        pos_dict = {
            "symbol": symbol,
            "name": name,
            "shares": round(shares, 4),
            "buy_price": round(effective_price, 4),
            "current_price": round(price, 4),  # Current market price is still mid"""
            
if old_buy in content:
    content = content.replace(old_buy, new_buy)
else:
    print("Could not find old_buy")


# 2. Update sell()
old_sell = """        pos = depot["positions"][symbol]
        shares = pos["shares"]
        revenue = shares * price
        pnl = (price - pos["buy_price"]) * shares
        pnl_pct = ((price - pos["buy_price"]) / pos["buy_price"]) * 100.0 if pos["buy_price"] > 0 else 0.0

        depot["cash"] += revenue
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        trade_record = {
            "type": "SELL",
            "symbol": symbol,
            "name": pos["name"],
            "product_type": pos.get("derivative_type", "STOCK"),
            "shares": round(shares, 4),
            "buy_price": round(pos["buy_price"], 2),
            "sell_price": round(price, 2),"""

new_sell = """        pos = depot["positions"][symbol]
        shares = pos["shares"]
        
        # Apply a simulated 0.2% Bid/Ask spread penalty on sell (receive less)
        SPREAD_PCT = 0.002
        effective_price = price * (1.0 - SPREAD_PCT)
        
        revenue = shares * effective_price
        pnl = (effective_price - pos["buy_price"]) * shares
        pnl_pct = ((effective_price - pos["buy_price"]) / pos["buy_price"]) * 100.0 if pos["buy_price"] > 0 else 0.0

        depot["cash"] += revenue
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        trade_record = {
            "type": "SELL",
            "symbol": symbol,
            "name": pos["name"],
            "product_type": pos.get("derivative_type", "STOCK"),
            "shares": round(shares, 4),
            "buy_price": round(pos["buy_price"], 4),
            "sell_price": round(effective_price, 4),"""

if old_sell in content:
    content = content.replace(old_sell, new_sell)
else:
    print("Could not find old_sell")

with open('src/portfolio.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated portfolio.py with simulated spread.")
