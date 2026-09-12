import codecs

with codecs.open('src/insider_whale_tracker.py', 'r', 'utf8') as f:
    content = f.read()

content = content.replace('trade_type = "UNBEKANNT"', 'trade_type = "🟠 UNBEKANNT"')
content = content.replace('trade_type = " KAUF"', 'trade_type = "🟩 KAUF"')
content = content.replace('trade_type = " VERKAUF"', 'trade_type = "🔴 VERKAUF"')
content = content.replace('trade_type = " ZUTEILUNG (GESCHENK)"', 'trade_type = "🟨 ZUTEILUNG (GESCHENK)"')

with codecs.open('src/insider_whale_tracker.py', 'w', 'utf8') as f:
    f.write(content)
print("Added emojis to insider tracker")
