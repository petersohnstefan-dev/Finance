import yfinance as yf
t = yf.Ticker('PLTR')
df = t.insider_transactions
if df is not None and not df.empty:
    for idx, row in df.head(10).iterrows():
        print(f"Value: {row.get('Value')}, Shares: {row.get('Shares')}, Text: {row.get('Text')}")
