import sys

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update buy()
old_buy_spread = """        # Apply a simulated 0.2% Bid/Ask spread penalty on buy (pay more)
        SPREAD_PCT = 0.002
        effective_price = price * (1.0 + SPREAD_PCT)"""

new_buy_spread = """        # Dynamische Spread-Berechnung (Bid/Ask Simulation)
        is_crypto = "-USD" in symbol.upper()
        is_derivative = derivative_meta is not None or symbol.startswith("KO")
        
        if is_derivative:
            SPREAD_PCT = 0.015  # 1.5% Spread für Hebelprodukte (wg. Emittenten-Risiko/Aufschlag)
        elif is_crypto:
            SPREAD_PCT = 0.005  # 0.5% Spread für Krypto-Börsen
        else:
            SPREAD_PCT = 0.002  # 0.2% für reguläre Aktien

        effective_price = price * (1.0 + SPREAD_PCT)"""

if old_buy_spread in content:
    content = content.replace(old_buy_spread, new_buy_spread)
else:
    print("Could not find old_buy_spread")

# 2. Update sell()
old_sell_spread = """        # Apply a simulated 0.2% Bid/Ask spread penalty on sell (receive less)
        SPREAD_PCT = 0.002
        effective_price = price * (1.0 - SPREAD_PCT)"""

new_sell_spread = """        # Dynamische Spread-Berechnung (Bid/Ask Simulation)
        is_crypto = "-USD" in symbol.upper()
        is_derivative = pos.get("derivative_meta") is not None or symbol.startswith("KO")
        
        if is_derivative:
            SPREAD_PCT = 0.015  # 1.5% 
        elif is_crypto:
            SPREAD_PCT = 0.005  # 0.5% 
        else:
            SPREAD_PCT = 0.002  # 0.2% 
            
        effective_price = price * (1.0 - SPREAD_PCT)"""

if old_sell_spread in content:
    content = content.replace(old_sell_spread, new_sell_spread)
else:
    print("Could not find old_sell_spread")


with open('src/portfolio.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated portfolio.py with dynamic spreads.")
