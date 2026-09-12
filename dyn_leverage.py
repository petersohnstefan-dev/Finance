import sys

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_logic = """                if not has_it and p > 0:
                    is_bearish = top_alert.get("direction") == "SHORT"
                    dir_str = "SHORT" if is_bearish else "LONG"
                    
                    turbo = DerivativeEngine.create_turbo_knockout(sym, name, p, direction=dir_str, target_leverage=10.0)
                    cert_price = turbo["cert_price"]
                    alloc = min(1500.0, dt_depot["cash"] * 0.9)
                    shares = alloc / cert_price
                    
                    reason_msg = f"⚡ Daytrade Momentum ({top_alert.get('change_1min_pct', 2.0):+.1f}% Spike) | 10x Hebel"
                    sl_price = cert_price * 0.8
                    
                    self.buy("day_trading", turbo["wkn"], turbo["name"], shares, cert_price,
                             reason=reason_msg,
                             stop_loss=sl_price, take_profit=None, derivative_meta=turbo)
                    actions_taken.append(f"KAUF {turbo['name']} (10x {dir_str} Daytrade)")"""

new_logic = """                if not has_it and p > 0:
                    is_bearish = top_alert.get("direction") == "SHORT"
                    dir_str = "SHORT" if is_bearish else "LONG"
                    
                    spike = top_alert.get('change_1min_pct', 2.0)
                    if spike > 3.5:
                        chosen_lev = 30.0
                    elif spike > 2.5:
                        chosen_lev = 10.0
                    elif spike > 1.5:
                        chosen_lev = 5.0
                    elif spike > 0.8:
                        chosen_lev = 2.0
                    else:
                        chosen_lev = 1.0 # Ohne Hebel
                    
                    alloc = min(1500.0, dt_depot["cash"] * 0.9)
                    
                    if chosen_lev > 1.0:
                        turbo = DerivativeEngine.create_turbo_knockout(sym, name, p, direction=dir_str, target_leverage=chosen_lev)
                        cert_price = turbo["cert_price"]
                        shares = alloc / cert_price
                        reason_msg = f"⚡ Daytrade Momentum ({spike:+.1f}% Spike) | {chosen_lev}x Hebel"
                        sl_price = cert_price * 0.75 # 25% Stop-Loss auf das Derivat
                        
                        self.buy("day_trading", turbo["wkn"], turbo["name"], shares, cert_price,
                                 reason=reason_msg,
                                 stop_loss=sl_price, take_profit=None, derivative_meta=turbo)
                        actions_taken.append(f"KAUF {turbo['name']} ({chosen_lev}x {dir_str})")
                    else:
                        # 1x Direktkauf der Aktie (Ohne Hebel)
                        shares = alloc / p
                        reason_msg = f"⚡ Daytrade Momentum ({spike:+.1f}% Spike) | 1x Direkt-Kauf (Aktie)"
                        sl_price = p * 0.98 # 2% Stop-Loss auf die Aktie (sehr eng beim Daytrading)
                        
                        self.buy("day_trading", sym, name, shares, p,
                                 reason=reason_msg,
                                 stop_loss=sl_price, take_profit=None)
                        actions_taken.append(f"KAUF {sym} (1x Direkt-Kauf)")"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('src/portfolio.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated portfolio.py with dynamic leverage.")
else:
    print("Could not find old logic in portfolio.py.")
