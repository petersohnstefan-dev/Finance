import codecs
import re

with codecs.open('src/portfolio.py', 'r', 'utf8') as f:
    content = f.read()

# Finding the block in Daytrader buy logic:
old_block = '''                real_name = next((r.get("name", sym) for r in scan_results if r["symbol"] == sym), sym)
                name = top_alert.get("name", real_name)
                p = top_alert.get("trigger_price", 10.0)'''

new_block = '''                real_name = next((r.get("name", sym) for r in scan_results if r["symbol"] == sym), sym)
                if real_name == sym:
                    try:
                        import yfinance as yf
                        info = yf.Ticker(sym).info
                        real_name = info.get('shortName') or info.get('longName') or sym
                    except:
                        pass
                name = top_alert.get("name") or real_name
                p = top_alert.get("trigger_price", 10.0)'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with codecs.open('src/portfolio.py', 'w', 'utf8') as f:
        f.write(content)
    print("Patched portfolio.py for daytrader names")
else:
    print("Could not find old block")
