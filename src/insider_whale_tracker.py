import yfinance as yf
import pandas as pd
from typing import Dict, List, Any
import datetime

# A watchlist of highly traded/relevant stocks to scan for live insider and whale data
WATCHLIST = [
    "NVDA", "AAPL", "MSFT", "TSLA", "PLTR", 
    "AMZN", "META", "GOOGL", "AMD", "SMCI",
    "CRWD", "PANW", "COIN", "MARA", "MSTR"
]

class LiveInsiderWhaleTracker:
    """Fetches 100% real live insider transactions and institutional holders via Yahoo Finance."""

    @staticmethod
    def get_live_insider_transactions() -> pd.DataFrame:
        """Fetches the latest real insider transactions (SEC Form 4) for the watchlist."""
        all_trades = []
        for ticker in WATCHLIST:
            try:
                stock = yf.Ticker(ticker)
                insiders = stock.insider_transactions
                if insiders is not None and not insiders.empty:
                    # Filter for actual buys/sells (usually 'P' for Purchase, 'S' for Sale)
                    # We just take the top 3 most recent transactions per ticker to keep it clean
                    recent = insiders.head(3).copy()
                    recent["Ticker"] = ticker
                    for idx, row in recent.iterrows():
                        all_trades.append({
                            "Ticker": ticker,
                            "Insider/Role": str(row.get("Insider Purchases", row.get("Insider", "Unknown"))),
                            "Date": str(row.get("Start Date", row.get("Transaction Start Date", "")))[:10],
                            "Shares": row.get("Shares", 0),
                            "Value ($)": row.get("Value", 0),
                        })
            except Exception as e:
                print(f"Error fetching insider data for {ticker}: {e}")
                
        if all_trades:
            df = pd.DataFrame(all_trades)
            # Sort by Date descending
            df = df.sort_values(by="Date", ascending=False).head(30)
            return df
        return pd.DataFrame()

    @staticmethod
    def get_live_whale_holders() -> pd.DataFrame:
        """Fetches the top institutional holders (Whales) for the watchlist."""
        all_holders = []
        for ticker in WATCHLIST:
            try:
                stock = yf.Ticker(ticker)
                holders = stock.institutional_holders
                if holders is not None and not holders.empty:
                    # Take the top 2 whales for each stock
                    top_whales = holders.head(2).copy()
                    for idx, row in top_whales.iterrows():
                        all_holders.append({
                            "Ticker": ticker,
                            "Whale / Institution": row.get("Holder", "Unknown"),
                            "Reported Date": str(row.get("Date Reported", ""))[:10],
                            "Shares Held": row.get("Shares", 0),
                            "Position Value ($)": row.get("Value", 0),
                        })
            except Exception as e:
                print(f"Error fetching whale data for {ticker}: {e}")
                
        if all_holders:
            return pd.DataFrame(all_holders)
        return pd.DataFrame()

if __name__ == "__main__":
    tracker = LiveInsiderWhaleTracker()
    print("Fetching live insiders...")
    print(tracker.get_live_insider_transactions())
    print("\nFetching live whales...")
    print(tracker.get_live_whale_holders())

class WhaleInsiderTracker(LiveInsiderWhaleTracker):
    @staticmethod
    def get_whale_sentiment_for_ticker(symbol: str) -> Dict[str, Any]:
        has_activity = False
        score_boost = 0
        whale_holders = []
        insider_buyers = []
        
        try:
            stock = yf.Ticker(symbol)
            # Fetch Whales
            holders = stock.institutional_holders
            if holders is not None and not holders.empty:
                for idx, row in holders.head(3).iterrows():
                    # Safely handle missing columns
                    pct = 0
                    if 'pctHeld' in holders.columns:
                        pct_val = row['pctHeld']
                        if not pd.isna(pct_val):
                            pct = pct_val * 100
                    
                    whale_holders.append({
                        'manager': str(row.get('Holder', 'Unknown')),
                        'fund': 'Institution',
                        'weight': f'{pct:.2f}',
                        'action': 'Aktiv'
                    })
                    has_activity = True
                    score_boost += 5
                    
            # Fetch Insiders
            insiders = stock.insider_transactions
            if insiders is not None and not insiders.empty:
                for idx, row in insiders.head(3).iterrows():
                    insider_buyers.append({
                        'insider': str(row.get('Insider Purchases', row.get('Insider', 'Unknown'))),
                        'role': 'Insider',
                        'amount': f"{row.get('Shares', 0)} shares",
                        'buy_price': '-',
                        'date': str(row.get('Start Date', row.get('Transaction Start Date', '')))[0:10],
                        'signal': 'SEC Form 4'
                    })
                    has_activity = True
                    score_boost += 10
        except Exception as e:
            print(f'Error fetching single ticker whale data: {e}')
            
        return {
            'has_activity': has_activity,
            'score_boost': min(25, score_boost),
            'whale_holders': whale_holders,
            'congress_buyers': [],  # No live congress data available
            'insider_buyers': insider_buyers
        }
