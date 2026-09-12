import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace("gemini-1.5-flash'", "gemini-1.5-flash-latest'")
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('src/ai_journal.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace("gemini-1.5-flash'", "gemini-1.5-flash-latest'")
with open('src/ai_journal.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched model names to gemini-1.5-flash-latest")
