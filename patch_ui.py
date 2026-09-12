import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("≥ +0.6% in < 60 Sek.", "≥ ±0.35% in < 60 Sek.")
content = content.replace("> +0,6 % getrieben", "> ±0,35 % (Long/Short) getrieben")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched UI strings.")
