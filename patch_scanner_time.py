import sys

with open('src/realtime_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()

import_str = "import time\n"
berlin_now = """import time
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

content = content.replace('now = datetime.datetime.now()', 'now = get_berlin_now()')

with open('src/realtime_scanner.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched realtime_scanner.py")
