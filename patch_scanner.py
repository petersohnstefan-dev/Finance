import sys

with open('src/realtime_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """    def scan_category(self, category_name: str = None) -> Dict[str, Any]:
        \"\"\"Scans all assets in a selected category in parallel.\"\"\"
        default_cat = list(WATCHLIST_CATEGORIES.keys())[0]
        if not category_name:
            category_name = default_cat
        tickers = WATCHLIST_CATEGORIES.get(category_name, WATCHLIST_CATEGORIES[default_cat])
        now = datetime.datetime.now()"""

new_code = """    def scan_category(self, category_name: str = None) -> Dict[str, Any]:
        \"\"\"Scans all assets in a selected category in parallel.\"\"\"
        keys = list(WATCHLIST_CATEGORIES.keys())
        if not keys:
            return {"count": 0, "alerts": [], "ticks": {}, "category": "Empty"}
            
        if not category_name or category_name not in WATCHLIST_CATEGORIES:
            category_name = keys[0]
            
        tickers = WATCHLIST_CATEGORIES[category_name]
        now = datetime.datetime.now()"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('src/realtime_scanner.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched realtime_scanner.py")
else:
    print("Could not find old_code")
