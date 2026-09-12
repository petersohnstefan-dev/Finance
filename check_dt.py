import json

with open('data/portfolios.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print("DAY TRADING POSITIONS:")
pos = d['portfolios']['day_trading']['positions']
for sym, data in pos.items():
    print(f"Symbol: {sym}")
    print(f"Name: {data.get('name')}")
    print(f"Underlying: {data.get('underlying_symbol')}")
    print(f"Buy Price: {data.get('buy_price')}")
    print(f"Current Price: {data.get('current_price')}")
    print("---")
