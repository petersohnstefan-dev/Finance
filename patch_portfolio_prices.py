import codecs
import re

with codecs.open('src/portfolio.py', 'r', 'utf8') as f:
    content = f.read()

old_fetch = '''        def fetch_single(sym):
            try:
                import yfinance as yf
                # Robust fallback for GitHub Actions IPs
                try:
                    data = yf.download(sym, period="1d", interval="1m", progress=False)
                    if not data.empty:
                        return sym, float(data['Close'].iloc[-1])
                except:
                    pass
                # Fallback to fast_info
                info = yf.Ticker(sym).fast_info
                px = info.last_price
                return sym, px
            except Exception:
                return sym, None'''

new_fetch = '''        def fetch_single(sym):
            try:
                import yfinance as yf
                ticker = yf.Ticker(sym)
                
                # 1. Try history (works best on GitHub Actions)
                try:
                    df = ticker.history(period="1d")
                    if not df.empty:
                        return sym, float(df['Close'].iloc[-1])
                except:
                    pass
                    
                # 2. Try fast_info
                try:
                    px = ticker.fast_info.last_price
                    return sym, px
                except:
                    pass
                    
                # 3. Try info dictionary
                info = ticker.info or {}
                px = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
                if px:
                    return sym, float(px)
                    
                return sym, None
            except Exception:
                return sym, None'''

content = content.replace(old_fetch, new_fetch)

with codecs.open('src/portfolio.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched portfolio.py prices")
