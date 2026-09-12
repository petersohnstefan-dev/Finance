import codecs
import re

with codecs.open('src/portfolio.py', 'r', 'utf8') as f:
    content = f.read()

# Replace using regex to handle line endings safely
content = re.sub(
    r'real_name = next\(\(r\.get\("name", sym\) for r in scan_results if r\["symbol"\] == sym\), sym\)[\s\r\n]+name = top_alert\.get\("name", real_name\)[\s\r\n]+p = top_alert\.get\("trigger_price", 10\.0\)',
    '''real_name = next((r.get("name", sym) for r in scan_results if r["symbol"] == sym), sym)
                if real_name == sym:
                    try:
                        import yfinance as yf
                        info = yf.Ticker(sym).info
                        real_name = info.get('shortName') or info.get('longName') or sym
                    except:
                        pass
                name = top_alert.get("name") or real_name
                p = top_alert.get("trigger_price", 10.0)''',
    content
)

with codecs.open('src/portfolio.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched portfolio.py with regex for names")
