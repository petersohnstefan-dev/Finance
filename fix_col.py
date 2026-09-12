with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_cfg = '"Ticker": st.column_config.TextColumn("Ticker", help="Börsenkürzel der Aktie"),'
new_cfg = '"WKN": st.column_config.TextColumn("WKN", help="Wertpapierkennnummer (z.B. 710000)"),'

if old_cfg in content:
    content = content.replace(old_cfg, new_cfg)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed second col_cfg!')
else:
    print('Not found!')
