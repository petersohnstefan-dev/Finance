daytrade_logic = """
        # ----------------------------------------------------------------------
        # 4. DAYTRADER DEPOT (Intraday / High Leverage / Momentum)
        # ----------------------------------------------------------------------
        dt_depot = self.data["portfolios"].get("day_trading")
        if dt_depot:
            for sym in list(dt_depot["positions"].keys()):
                pos = dt_depot["positions"][sym]
                curr_p = pos["current_price"]
                buy_p = pos["buy_price"]
                gain_pct = ((curr_p - buy_p) / buy_p * 100.0) if buy_p > 0 else 0.0

                peak_p = max(pos.get("peak_price", buy_p), curr_p)
                pos["peak_price"] = peak_p

                # Very tight Trailing Profit Ratchet
                if gain_pct >= 5.0:
                    pos["stop_loss"] = max(pos.get("stop_loss", 0), round(buy_p * 1.02, 2))
                if gain_pct >= 10.0:
                    pos["stop_loss"] = max(pos.get("stop_loss", 0), round(peak_p * 0.95, 2))  # 5% trailing room (tighter)

                # Intraday strict stop-loss
                if pos.get("stop_loss") and curr_p <= pos["stop_loss"]:
                    if curr_p >= buy_p:
                        self.sell("day_trading", sym, curr_p, reason=f"🎯 Daytrade-Trailing-Stop gegriffen (+{gain_pct:.1f}%)")
                        actions_taken.append(f"VERKAUF {sym} (Daytrade-Profit +{gain_pct:.1f}%)")
                    else:
                        self.sell("day_trading", sym, curr_p, reason=f"🚨 Daytrade Notbremse (Stop-Loss {gain_pct:.1f}%)")
                        actions_taken.append(f"VERKAUF {sym} (Daytrade-Stop)")
                    continue

                # Automatic End-of-Day Derisking (if >15:00 and in profit)
                hour = get_berlin_now().hour
                if hour >= 21 and gain_pct > 2.0:
                    self.sell("day_trading", sym, curr_p, reason=f"🛡️ Intraday EOD-Derisking (+{gain_pct:.1f}%)")
                    actions_taken.append(f"VERKAUF {sym} (EOD +{gain_pct:.1f}%)")
                    continue

            # Buy new highly leveraged positions
            if dt_depot["cash"] >= 1000.0 and len(dt_depot["positions"]) < 5 and rt_alerts:
                top_alert = rt_alerts[0]
                sym = top_alert["symbol"]
                name = top_alert.get("name", sym)
                p = top_alert.get("trigger_price", 10.0)
                
                # Check if we already have it
                has_it = False
                for existing_sym in dt_depot["positions"]:
                    if sym in existing_sym: # handles derivative WKNs which contain sym
                        has_it = True
                        break
                
                if not has_it and p > 0:
                    is_bearish = top_alert.get("direction") == "SHORT"
                    dir_str = "SHORT" if is_bearish else "LONG"
                    
                    turbo = DerivativeEngine.create_turbo_knockout(sym, name, p, direction=dir_str, target_leverage=10.0)
                    cert_price = turbo["cert_price"]
                    alloc = min(1500.0, dt_depot["cash"] * 0.9) # Smaller positions max 1500
                    shares = alloc / cert_price
                    
                    reason_msg = f"⚡ Daytrade Momentum ({top_alert.get('change_1min_pct', 2.0):+.1f}% Spike) | 10x Hebel"
                    sl_price = cert_price * 0.8 # 20% max loss on cert
                    
                    self.buy("day_trading", turbo["wkn"], turbo["name"], shares, cert_price,
                             reason=reason_msg,
                             stop_loss=sl_price, take_profit=None, derivative_meta=turbo)
                    actions_taken.append(f"KAUF {turbo['name']} (10x {dir_str} Daytrade)")
"""

import sys

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, l in enumerate(lines):
    if 'self._save()' in l and 'break' in lines[i-3]:
        # We are at the end of auto_trade_check
        new_lines.extend(daytrade_logic.splitlines(True))
        new_lines.append(l)
    elif 'for k in ["short_term", "medium_term", "long_term"]:' in l:
        new_lines.append(l.replace('["short_term", "medium_term", "long_term"]', '["short_term", "medium_term", "long_term", "day_trading"]'))
    else:
        new_lines.append(l)

with open('src/portfolio.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done injecting daytrade logic.')
