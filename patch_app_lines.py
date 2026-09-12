import codecs

with codecs.open('app.py', 'r', 'utf8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    
    # Krypto row in h_tab1
    if "6. Krypto On-Chain" in line:
        new_lines.append("                | ** 7. Live SEC Form 4 (Insider-Boost)**| **+15 bis +25 Punkte** | Form 4 Filings: Vorstände/CEOs investieren substanziell eigenes Geld. Stock Grants ($0) werden herausgefiltert! |\n")
    
    # SEC Form 4 row in h_tab2
    if "2. SEC Form 4" in line and "Kongress-Trades" in line:
        # We replace the line we just appended
        new_lines.pop()
        new_lines.append("                | ** 2. SEC Form 4 & Kongress-Trades** | **20 % (Live Boost)** | Direkter Score-Boost bei harten Cash-Käufen durch das C-Level. Ausschluss von Null-Dollar-Vergütungen! |\n")
        
    # Insider row in h_tab3
    if "2. Insider-" in line and "Whale-Convictions" in line:
        new_lines.pop()
        new_lines.append("                | ** 2. Insider- & Whale-Convictions** | **25 % (Live Boost)** | Star-Investoren & Director's Dealings. Wenn CEOs mit Eigenkapital einsteigen, schlägt der Scanner aggressiver an. |\n")

with codecs.open('app.py', 'w', 'utf8') as f:
    f.writelines(new_lines)
print("Line-by-line patched app.py!")
