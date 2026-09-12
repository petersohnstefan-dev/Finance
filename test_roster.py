import yfinance as yf
import pandas as pd

def test_ticker(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    roster = stock.insider_roster_holders
    insiders = stock.insider_transactions
    
    if insiders is not None:
        for _, row in insiders.head(5).iterrows():
            sec_name = str(row.get('Insider Purchases', row.get('Insider', '')))
            total_owned = 'Unknown'
            
            if roster is not None and not roster.empty:
                match = roster[roster['Name'] == sec_name]
                if not match.empty:
                    dir_shares = match.iloc[0].get('Shares Owned Directly')
                    indir_shares = match.iloc[0].get('Shares Owned Indirectly')
                    total = 0
                    if pd.notna(dir_shares): total += float(dir_shares)
                    if pd.notna(indir_shares): total += float(indir_shares)
                    total_owned = total
            
            shares = row.get('Shares', 0)
            if total_owned != 'Unknown' and total_owned > 0 and pd.notna(shares):
                ratio = (float(shares) / total_owned) * 100
                print(f'{ticker_symbol} | {sec_name} | Trade: {shares} shares | Total Owned: {total_owned} | Trade is {ratio:.2f}% of holdings')
            else:
                print(f'{ticker_symbol} | {sec_name} | Trade: {shares} shares | Total Owned: {total_owned}')

test_ticker('CRWD')
test_ticker('NVDA')
test_ticker('AAPL')
