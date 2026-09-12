import sys

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_logic = """                peak_p = max(pos.get("peak_price", buy_p), curr_p)
                pos["peak_price"] = peak_p

                # Very tight Trailing Profit Ratchet"""

new_logic = """                peak_p = max(pos.get("peak_price", buy_p), curr_p)
                pos["peak_price"] = peak_p

                # Check Knock-Out
                if pos.get("is_knocked_out"):
                    self.sell("day_trading", sym, 0.001, reason="❌ Knock-Out Barriere berührt (Totalverlust)")
                    actions_taken.append(f"KNOCK-OUT {sym}")
                    continue

                # Very tight Trailing Profit Ratchet"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('src/portfolio.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched day_trading knockout check.")
else:
    print("Could not find old_logic in src/portfolio.py")
