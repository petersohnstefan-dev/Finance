import sys

with open('src/market_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()

inj = """
        try:
            from src.db import PortfolioDB
            pdb = PortfolioDB()
            top_radars = sorted([r for r in results if r.get("breakout_score", 0) > 0], key=lambda x: x.get("breakout_score", 0), reverse=True)[:5]
            if top_radars:
                # Add theme string for the UI
                for t in top_radars:
                    t["theme"] = t.get("breakout_status", "Radar Hit")
                pdb.record_radar_signals(top_radars)
        except Exception as e:
            print("Radar record error:", e)

        sys.stdout.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}]"""

content = content.replace("        sys.stdout.write(f\"[{datetime.datetime.now().strftime('%H:%M:%S')}]", inj)

with open('src/market_scanner.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated market_scanner.py")
