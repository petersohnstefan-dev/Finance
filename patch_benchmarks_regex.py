import codecs
import re

with codecs.open('app.py', 'r', 'utf8') as f:
    content = f.read()

# Replace fetch_index_benchmarks
new_fetch = '''    def fetch_index_benchmarks(start_date: str):
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

content = re.sub(r'    def fetch_index_benchmarks\(start_date: str\):.*?(?=\n    @st\.fragment)', new_fetch + '\n', content, flags=re.DOTALL)

# Replace mapping logic
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

content = re.sub(r'            # 2\.5 Index Benchmarks.*?norm_vals = \(mapped / base_val\) \* 10000\.0', new_mapping, content, flags=re.DOTALL)

with codecs.open('app.py', 'w', 'utf8') as f:
    f.write(content)
print("Regex patch successful")
