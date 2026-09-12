import sys

with open('src/realtime_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """                if change_pct >= 0.6:
                    alert = {
                        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "time_str": now.strftime("%H:%M:%S"),
                        "symbol": sym,
                        "trigger_price": round(px, 2),
                        "change_1min_pct": round(change_pct, 2),
                        "urgency": "⚡ EXTREM (Sofortiger Intraday-Ausbruch)",
                        "message": f"🚨 {sym} explodiert um {change_pct:+.2f}% in <60 Sek.! Short-Squeeze-Druck aktiv."
                    }
                    new_alerts.append(alert)
                    self._record_alert(alert)"""

new_code = """                if abs(change_pct) >= 0.35:
                    direction = "LONG" if change_pct > 0 else "SHORT"
                    msg = f"🚨 {sym} explodiert um {change_pct:+.2f}% in <60 Sek.! Short-Squeeze-Druck aktiv." if direction == "LONG" else f"🚨 {sym} stürzt um {change_pct:+.2f}% ab! Panik-Verkauf aktiv."
                    
                    alert = {
                        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "time_str": now.strftime("%H:%M:%S"),
                        "symbol": sym,
                        "direction": direction,
                        "trigger_price": round(px, 2),
                        "change_1min_pct": round(abs(change_pct), 2),
                        "urgency": "⚡ EXTREM (Sofortiger Intraday-Ausbruch)",
                        "message": msg
                    }
                    new_alerts.append(alert)
                    self._record_alert(alert)"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('src/realtime_scanner.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched realtime_scanner.py")
else:
    print("Could not find old_code")
