import sys

with open('src/db.py', 'r', encoding='utf-8') as f:
    content = f.read()

# First, insert get_berlin_now
import_str = "from typing import Dict, Any, List, Optional\n"
berlin_now = """from typing import Dict, Any, List, Optional
from zoneinfo import ZoneInfo

BERLIN_TZ = ZoneInfo("Europe/Berlin")
def get_berlin_now() -> datetime.datetime:
    try:
        return datetime.datetime.now(BERLIN_TZ)
    except Exception:
        return datetime.datetime.utcnow() + datetime.timedelta(hours=2)
"""
if "get_berlin_now" not in content:
    content = content.replace(import_str, berlin_now)

content = content.replace('datetime.datetime.now()', 'get_berlin_now()')

with open('src/db.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched db.py")

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()
# Replace in buy/sell
content = content.replace('datetime.datetime.now().strftime("%Y-%m-%d %H:%M', 'get_berlin_now().strftime("%Y-%m-%d %H:%M')
with open('src/portfolio.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched portfolio.py")
