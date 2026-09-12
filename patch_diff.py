import sys

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('if (datetime.datetime.now() - atime).total_seconds() > 300:', 'if (get_berlin_now() - atime.replace(tzinfo=BERLIN_TZ)).total_seconds() > 300:')

with open('src/portfolio.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched timezone diff in portfolio.py")
