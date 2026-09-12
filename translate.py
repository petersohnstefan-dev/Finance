with open('src/insider_whale_tracker.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"Ticker": ticker,', '"Aktie (Ticker)": ticker,')
content = content.replace('"Insider/Role":', '"Käufer / Vorstand":')
content = content.replace('"Date":', '"Datum der SEC-Meldung":')
content = content.replace('"Shares":', '"Anzahl Aktien":')
content = content.replace('"Value ($)":', '"Transaktionswert (USD)":')

content = content.replace('"Whale / Institution":', '"Großaktionär (Fonds)":')
content = content.replace('"Reported Date":', '"Stichtag der Meldung":')
content = content.replace('"Shares Held":', '"Aktien im Besitz":')
content = content.replace('"Position Value ($)":', '"Gesamtwert (USD)":')

content = content.replace('df.sort_values(by="Date"', 'df.sort_values(by="Datum der SEC-Meldung"')

with open('src/insider_whale_tracker.py', 'w', encoding='utf-8') as f:
    f.write(content)
