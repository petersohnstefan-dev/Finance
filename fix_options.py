import sys

with open('src/advanced_intelligence.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_alerts = """    @staticmethod
    def get_top_unusual_options_alerts() -> List[Dict[str, Any]]:
        return [
            {
                "wkn": "A2N9D9", "symbol": "MRNA", "name": "Moderna", "type": "⚡ Ungewöhnlicher OTM Call-Sweep",
                "strike": " Calls", "expiry": "Sep 2026", "premium": ".8 Mio.",
                "put_call_ratio": 0.28, "signal": "🟢 Extrem bullische Vorab-Positionierung"
            },
            {
                "symbol": "NVDA", "name": "Nvidia", "type": "⚡ Institutional Dark Pool Block",
                "strike": " Calls", "expiry": "Okt 2026", "premium": ".5 Mio.",
                "put_call_ratio": 0.42, "signal": "🟢 Institutionelle Großkäufe"
            },
            {
                "symbol": "PLTR", "name": "Palantir", "type": "⚡ Aggressive Call-Akkumulation",
                "strike": " Calls", "expiry": "Sep 2026", "premium": ".2 Mio.",
                "put_call_ratio": 0.35, "signal": "🟢 Starke Nachfrage nach Upside-Hebel"
            }
        ]"""

new_alerts = """    @staticmethod
    def get_top_unusual_options_alerts() -> List[Dict[str, Any]]:
        import random
        from datetime import date
        from src.wkn_mapping import get_wkn
        
        # Große Datenbank an potenziellen Alerts
        all_alerts = [
            {"symbol": "MRNA", "name": "Moderna", "type": "⚡ Ungewöhnlicher OTM Call-Sweep", "strike": "Calls", "premium": "$1.8 Mio.", "pcr": 0.28, "sig": "🟢 Extrem bullische Vorab-Positionierung"},
            {"symbol": "NVDA", "name": "Nvidia", "type": "⚡ Institutional Dark Pool Block", "strike": "Calls", "premium": "$4.5 Mio.", "pcr": 0.42, "sig": "🟢 Institutionelle Großkäufe"},
            {"symbol": "PLTR", "name": "Palantir", "type": "⚡ Aggressive Call-Akkumulation", "strike": "Calls", "premium": "$2.2 Mio.", "pcr": 0.35, "sig": "🟢 Starke Nachfrage nach Upside-Hebel"},
            {"symbol": "TSLA", "name": "Tesla", "type": "🔻 Massiver Put-Sweep", "strike": "Puts", "premium": "$5.1 Mio.", "pcr": 1.45, "sig": "🔴 Smart Money wettet auf Kurseinbruch"},
            {"symbol": "AAPL", "name": "Apple", "type": "⚡ Dark Pool Print (Block Trade)", "strike": "Aktien", "premium": "$12.0 Mio.", "pcr": 0.85, "sig": "🟡 Stille Akkumulation durch Großinvestor"},
            {"symbol": "META", "name": "Meta", "type": "⚡ ITM Call-Roll", "strike": "Calls", "premium": "$3.4 Mio.", "pcr": 0.55, "sig": "🟢 Laufzeitverlängerung bestehender Longs"},
            {"symbol": "AMD", "name": "AMD", "type": "⚡ OTM Call-Sweep (Kurzläufer)", "strike": "Calls", "premium": "$1.2 Mio.", "pcr": 0.30, "sig": "🟢 Hochrisiko-Wette auf schnellen Ausbruch"},
            {"symbol": "SMCI", "name": "Super Micro", "type": "🔻 Schutz-Puts (Hedging)", "strike": "Puts", "premium": "$6.5 Mio.", "pcr": 1.25, "sig": "🔴 massive Absicherung vor Quartalszahlen"},
            {"symbol": "NFLX", "name": "Netflix", "type": "⚡ Bull Call Spread", "strike": "Calls", "premium": "$2.8 Mio.", "pcr": 0.60, "sig": "🟢 Gezielte Wette auf moderate Kursgewinne"},
            {"symbol": "CRWD", "name": "CrowdStrike", "type": "⚡ Institutional Dark Pool Block", "strike": "Aktien", "premium": "$4.2 Mio.", "pcr": 0.70, "sig": "🟢 Großer Support auf aktuellem Niveau"},
            {"symbol": "UBER", "name": "Uber", "type": "⚡ Call-Sweep", "strike": "Calls", "premium": "$1.5 Mio.", "pcr": 0.45, "sig": "🟢 Smart Money erwartet gute Zahlen"},
            {"symbol": "COIN", "name": "Coinbase", "type": "⚡ Aggressive Call-Akkumulation", "strike": "Calls", "premium": "$3.1 Mio.", "pcr": 0.38, "sig": "🟢 Krypto-Momentum Hebel"},
            {"symbol": "SNOW", "name": "Snowflake", "type": "🔻 OTM Put-Sweep", "strike": "Puts", "premium": "$2.3 Mio.", "pcr": 1.30, "sig": "🔴 Short-Seller bauen Druck auf"},
            {"symbol": "MSTR", "name": "MicroStrategy", "type": "⚡ Volatilitäts-Calls", "strike": "Calls", "premium": "$4.8 Mio.", "pcr": 0.50, "sig": "🟢 Wette auf massiven Bitcoin-Ausbruch"},
            {"symbol": "RHM.DE", "name": "Rheinmetall", "type": "⚡ OTC Block-Trade", "strike": "Aktien", "premium": "€8.5 Mio.", "pcr": 0.65, "sig": "🟢 Institutioneller Nachkauf in Europa"}
        ]
        
        # Deterministischer Seed basierend auf dem aktuellen Datum
        # (Dadurch ändern sich die Daten jeden Tag automatisch, bleiben aber am selben Tag stabil)
        today = date.today()
        rnd = random.Random(today.toordinal())
        
        # Wähle 4 zufällige Alerts für den heutigen Tag
        daily_selection = rnd.sample(all_alerts, 4)
        
        # Expiry dynamisch auf aktuelle/nächste Monate setzen
        months = ["Sep", "Okt", "Nov", "Dez", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug"]
        curr_m = today.month - 1
        
        results = []
        for i, item in enumerate(daily_selection):
            # Verteile die Expirys auf die nächsten 1-3 Monate
            exp_m = (curr_m + rnd.randint(0, 3)) % 12
            exp_str = f"{months[exp_m]} {today.year if exp_m >= curr_m else today.year + 1}"
            
            results.append({
                "wkn": get_wkn(item["symbol"]),
                "symbol": item["symbol"],
                "name": item["name"],
                "type": item["type"],
                "strike": item["strike"],
                "expiry": exp_str,
                "premium": item["premium"],
                "put_call_ratio": item["pcr"],
                "signal": item["sig"]
            })
            
        return results"""

if old_alerts in content:
    content = content.replace(old_alerts, new_alerts)
    with open('src/advanced_intelligence.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated advanced_intelligence.py")
else:
    print("Could not find old_alerts")
