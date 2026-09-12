import codecs
import re

with codecs.open('app.py', 'r', 'utf8') as f:
    content = f.read()

old_func = '''    def fetch_index_benchmarks(start_date: str):
        try:
            import yfinance as yf
            tickers = {"DAX": "^GDAXI", "Nasdaq": "^IXIC", "Dow": "^DJI", "S&P 500": "^GSPC"}
            # Fetch daily data
            idx_data = yf.download(list(tickers.values()), start=start_date, progress=False)['Close']
            # Make sure index is string YYYY-MM-DD
            idx_data.index = pd.to_datetime(idx_data.index).strftime("%Y-%m-%d")
            return idx_data, tickers
        except Exception as e:
            return None, None'''

new_func = '''    def fetch_index_benchmarks(start_date: str):
        try:
            import yfinance as yf
            import pandas as pd
            from zoneinfo import ZoneInfo
            tickers = {"DAX": "^GDAXI", "Nasdaq": "^IXIC", "Dow": "^DJI", "S&P 500": "^GSPC"}
            # Fetch hourly intraday data for a smooth curve
            idx_data = yf.download(list(tickers.values()), start=start_date, interval="1h", progress=False)['Close']
            # Forward fill NaNs so that EU indices stay flat while US is open and vice-versa
            idx_data = idx_data.ffill()
            # Convert timezone to Berlin and format exactly as "YYYY-MM-DD HH:00"
            idx_data.index = idx_data.index.tz_convert(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:00")
            # Remove duplicate hours if any
            idx_data = idx_data[~idx_data.index.duplicated(keep='last')]
            return idx_data, tickers
        except Exception as e:
            return None, None'''

content = content.replace(old_func, new_func)

old_mapping = '''            # 2.5 Index Benchmarks
            try:
                start_date_str = pd.to_datetime(eq_df["date"].iloc[0]).strftime("%Y-%m-%d")
                idx_data, tickers = fetch_index_benchmarks(start_date_str)
                if idx_data is not None:
                    eq_df["date_only"] = pd.to_datetime(eq_df["date"]).dt.strftime("%Y-%m-%d")
                    colors = {"DAX": "#facc15", "Nasdaq": "#a855f7", "S&P 500": "#ec4899", "Dow": "#22d3ee"}
                    
                    for t_name, ticker in tickers.items():
                        s = idx_data[ticker].dropna()
                        if not s.empty:
                            base_val = s.iloc[0]
                            mapped = eq_df["date_only"].map(s).ffill()
                            norm_vals = (mapped / base_val) * 10000.0'''

new_mapping = '''            # 2.5 Index Benchmarks
            try:
                start_date_str = pd.to_datetime(eq_df["date"].iloc[0]).strftime("%Y-%m-%d")
                idx_data, tickers = fetch_index_benchmarks(start_date_str)
                if idx_data is not None:
                    # Match precisely on the hour
                    eq_df["date_hour"] = pd.to_datetime(eq_df["date"]).dt.strftime("%Y-%m-%d %H:00")
                    colors = {"DAX": "#facc15", "Nasdaq": "#a855f7", "S&P 500": "#ec4899", "Dow": "#22d3ee"}
                    
                    for t_name, ticker in tickers.items():
                        s = idx_data[ticker].dropna()
                        if not s.empty:
                            base_val = s.iloc[0]
                            # Map hourly values and ffill across weekends or missing data
                            mapped = eq_df["date_hour"].map(s).ffill().bfill()
                            norm_vals = (mapped / base_val) * 10000.0'''

content = content.replace(old_mapping, new_mapping)

with codecs.open('app.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched app.py benchmarks")
