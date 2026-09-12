import sys

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_logic = """                # Check if we already have it
                has_it = False
                for existing_sym in dt_depot["positions"]:
                    if sym in existing_sym:
                        has_it = True
                        break
                
                if not has_it and p > 0:"""

new_logic = """                # 1. Check if we already hold a position for this underlying
                has_it = False
                for existing_sym, pos in dt_depot["positions"].items():
                    if existing_sym == sym or pos.get("underlying_symbol") == sym:
                        has_it = True
                        break
                
                # 2. Check if we already traded it today (prevent revenge trading / infinite loop)
                recently_traded = False
                try:
                    today_str = get_berlin_now().strftime("%Y-%m-%d")
                    recent_trades = self.db.get_trades("day_trading")
                    if not recent_trades:
                        recent_trades = reversed(dt_depot.get("history", []))
                    for t in recent_trades:
                        t_date = t.get("executed_at") or t.get("date", "")
                        if not t_date.startswith(today_str):
                            continue
                        t_sym = t.get("symbol", "")
                        t_name = t.get("name", "")
                        t_ticker = t.get("ticker", "")
                        if t_sym == sym or sym in t_name or sym in t_ticker:
                            recently_traded = True
                            break
                except:
                    pass

                # 3. Check if alert is fresh (< 5 mins old)
                is_fresh = True
                alert_ts = top_alert.get("timestamp")
                if alert_ts:
                    try:
                        import datetime
                        atime = datetime.datetime.strptime(alert_ts, "%Y-%m-%d %H:%M:%S")
                        if (datetime.datetime.now() - atime).total_seconds() > 300:
                            is_fresh = False
                    except:
                        pass
                
                if not has_it and not recently_traded and is_fresh and p > 0:"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('src/portfolio.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched day_trading buy logic.")
else:
    print("Could not find old_logic in src/portfolio.py")
