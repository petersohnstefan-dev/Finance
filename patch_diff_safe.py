import sys

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('if (get_berlin_now() - atime.replace(tzinfo=BERLIN_TZ)).total_seconds() > 300:', 'if (get_berlin_now().replace(tzinfo=None) - atime).total_seconds() > 300:')

with open('src/portfolio.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched naive timezone diff")
