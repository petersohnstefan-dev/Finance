import codecs

with codecs.open('app.py', 'r', 'utf8') as f:
    content = f.read()

# h_tab1 injection
old_short = "| ** 6. Krypto On-Chain & Derivate**| **15 %** | Krypto-Funding-Rates (+6.8% gesund), Exchange-Netto-Abflüsse (Cold Storage) |"
new_short = old_short + "\n                | ** 7. Live SEC Form 4 (Insider-Boost)**| **+15 bis +25 Punkte** | Form 4 Filings: Vorstände/CEOs investieren substanziell eigenes Geld. Stock Grants ($0) werden herausgefiltert! |"

content = content.replace(old_short, new_short)

# h_tab2 injection (Mittelfristiges Depot)
# Look for where SEC Form 4 is currently mentioned, we can update it!
old_mid = "| ** 2. SEC Form 4 & Kongress-Trades** | **20 %** | Vorstands-Käufe (CEO/Director) & US-Kongress-Disclosures (Nancy Pelosi, House Committees) |"
new_mid = "| ** 2. SEC Form 4 & Kongress-Trades** | **20 % (Live Boost)** | Direkter Score-Boost bei harten Cash-Käufen durch das C-Level. Ausschluss von Null-Dollar-Vergütungen! |"

content = content.replace(old_mid, new_mid)

# h_tab3 injection (Langfrist)
old_long = "| ** 2. Insider- & Whale-Convictions** | **25 %** | Star-Investoren (Warren Buffett, Bill Ackman) & Directors' Dealings der Vorstände |"
new_long = "| ** 2. Insider- & Whale-Convictions** | **25 % (Live Boost)** | Star-Investoren & Director's Dealings. Wenn CEOs mit Eigenkapital einsteigen, schlägt der Scanner aggressiver an. |"

content = content.replace(old_long, new_long)

with codecs.open('app.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched app.py with correct insider docs!")
