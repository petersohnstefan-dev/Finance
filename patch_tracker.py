import codecs
import re

with codecs.open('src/insider_whale_tracker.py', 'r', 'utf8') as f:
    content = f.read()

# Add the new column logic
def replacer(match):
    return match.group(0) + '''
                            "Transaktionswert ($)": row.get("Value", 0),'''

content = re.sub(r'"Anzahl Aktien": row\.get\("Shares", 0\),', replacer, content)

with codecs.open('src/insider_whale_tracker.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched tracker!")
