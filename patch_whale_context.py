import codecs

with codecs.open('src/insider_whale_tracker.py', 'r', 'utf-8') as f:
    content = f.read()

# We need to find the whale dictionary and replace it
import re

def repl(match):
    return """
                        pct_held = row.get("pctHeld", 0)
                        if pd.isna(pct_held): pct_held = 0
                        
                        pct_change = row.get("pctChange", 0)
                        if pd.isna(pct_change): pct_change = 0

                        val = row.get("Value", 0)
                        if pd.isna(val): val = 0

                        all_holders.append({
                            "Aktie (Ticker)": ticker,
                            "Unternehmen": TICKER_NAMES.get(ticker, ticker),
                            "Großaktionär (Fonds)": row.get("Holder", "Unknown"),
                            "Anteil am Unternehmen": f"{pct_held * 100:.2f} %",
                            "Veränderung (Quartal)": f"{pct_change * 100:+.2f} %",
                            "Aktien im Besitz": row.get("Shares", 0),
                            "Gesamtwert (USD)": f"${val:,.0f}",
                            "Stichtag": str(row.get("Date Reported", ""))[:10],
                        })"""

# Use regex to replace the old append block safely
pattern = re.compile(r'all_holders\.append\(\{.*?"Gesamtwert \(USD\)": row\.get\("Value", 0\),\s*\}\)', re.DOTALL)
content = pattern.sub(repl, content)

# Fix the broken unicode in the file since PowerShell messed it up earlier
content = content.replace("Kufer", "Käufer").replace("GroYaktionr", "Großaktionär")

with codecs.open('src/insider_whale_tracker.py', 'w', 'utf-8') as f:
    f.write(content)
print("Done")
