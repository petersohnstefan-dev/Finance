import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_hardcode = "HEUTE IST DER 29.08.2026"
new_hardcode = "HEUTE IST DER {datetime.datetime.now().strftime('%d.%m.%Y')}"

# wait, I need to import datetime in app.py if not already. But datetime is used in get_berlin_now(). Wait, get_berlin_now() is not in app.py directly.
# Let's just use time module or just leave it since the prompt string is formatted.
