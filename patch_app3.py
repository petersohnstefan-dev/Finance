import codecs
import re

with codecs.open('app.py', 'r', 'utf8') as f:
    content = f.read()

# Replace Kurzfrist
content = re.sub(
    r'(\|\s*\*\*\s*6\.\s*Krypto On-Chain.*?\|)',
    r'\g<1>\n                | ** 7. Live SEC Form 4 (Insider-Boost)** | **+15 bis +25 Punkte** | Form 4 Filings: Vorstände/CEOs investieren eigenes Geld. Stock Grants ($0) werden herausgefiltert! |',
    content
)

# Replace Mittelfrist
content = re.sub(
    r'\|\s*\*\*\s*2\.\s*SEC Form 4 & Kongress-Trades\s*\*\*.*?\|.*?\|.*?\|',
    r'| ** 2. SEC Form 4 & Kongress-Trades** | **20 % (Live Boost)** | Direkter Score-Boost bei Cash-Käufen durch das C-Level. Ausschluss von Null-Dollar-Vergütungen! |',
    content
)

# Replace Langfrist
content = re.sub(
    r'\|\s*\*\*\s*2\.\s*Insider- & Whale-Convictions\s*\*\*.*?\|.*?\|.*?\|',
    r'| ** 2. Insider- & Whale-Convictions** | **25 % (Live Boost)** | Star-Investoren & Director\'s Dealings. Wenn CEOs mit Eigenkapital einsteigen, schlägt der Scanner aggressiver an. |',
    content
)

with codecs.open('app.py', 'w', 'utf8') as f:
    f.write(content)
print("Regex patched app.py!")
