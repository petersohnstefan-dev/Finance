import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("Hebel von 1x (Direkt-Kauf), 2x, 5x, 10x oder bis zu 30x", "Hebel von 2x, 5x, 10x, 15x oder bis zu 30x")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched UI leverage strings.")
