import yfinance as yf
import pandas as pd
from typing import Dict, List, Any
import datetime

WATCHLIST = [
    "NVDA", "AAPL", "MSFT", "TSLA", "PLTR", 
    "AMZN", "META", "GOOGL", "AMD", "SMCI",
    "CRWD", "PANW", "COIN", "MARA", "MSTR"
]

TICKER_NAMES = {
    "NVDA": "NVIDIA Corp.",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corp.",
    "TSLA": "Tesla Inc.",
    "PLTR": "Palantir Tech.",
    "AMZN": "Amazon.com",
    "META": "Meta Platforms",
    "GOOGL": "Alphabet Inc.",
    "AMD": "Advanced Micro Devices",
    "SMCI": "Super Micro Comp.",
    "CRWD": "CrowdStrike",
    "PANW": "Palo Alto Networks",
    "COIN": "Coinbase Global",
    "MARA": "Marathon Digital",
    "MSTR": "MicroStrategy"
}

class LiveInsiderWhaleTracker:
    @staticmethod
    def get_live_insider_transactions() -> pd.DataFrame:
        all_trades = []
        for ticker in WATCHLIST:
            try:
                stock = yf.Ticker(ticker)
                insiders = stock.insider_transactions
                if insiders is not None and not insiders.empty:
                    recent = insiders.head(5).copy()
                    for idx, row in recent.iterrows():
                        text = str(row.get("Text", "-"))
                        
                        trade_type = "🟠 UNBEKANNT"
                        if "Purchase" in text or "Buy" in text:
                            trade_type = "🟩 KAUF"
                        elif "Sale" in text or "Sell" in text:
                            trade_type = "🔴 VERKAUF"
                        elif "Grant" in text or "Award" in text or "Gift" in text or "0.00 per share" in text:
                            trade_type = "🟨 ZUTEILUNG (GESCHENK)"
                            
                        shares = row.get("Shares", 0)
                        
                        all_trades.append({
                            "Datum": str(row.get("Start Date", row.get("Transaction Start Date", "")))[:10],
                            "Aktie": ticker,
                            "Typ": trade_type,
                            "Insider / Person": str(row.get("Insider Purchases", row.get("Insider", "Unknown"))),
                            "Titel (Rolle)": str(row.get("Position", "-")),
                            "Anzahl": shares,
                            "Wert ($)": row.get("Value", 0),
                            "Details zur Transaktion": text
                        })
            except Exception as e:
                print(f"Error fetching insider data for {ticker}: {e}")
                
        if all_trades:
            import math
            df = pd.DataFrame(all_trades)
            
            def format_value(val):
                if isinstance(val, (int, float)) and not math.isnan(val) and val > 0:
                    return f"${val:,.0f}"
                return "$0"
                
            def format_shares(val):
                if isinstance(val, (int, float)) and not math.isnan(val):
                    return f"{val:,.0f}"
                return str(val)
            
            def format_text(txt):
                if isinstance(txt, str) and "0.00 per share" in txt:
                    return txt + " (Praktisch geschenkt erhalten!)"
                return txt
                
            if "Wert ($)" in df.columns:
                df["Wert ($)"] = df["Wert ($)"].apply(format_value)
                
            if "Anzahl" in df.columns:
                df["Anzahl"] = df["Anzahl"].apply(format_shares)
            
            if "Details zur Transaktion" in df.columns:
                df["Details zur Transaktion"] = df["Details zur Transaktion"].apply(format_text)
                
            return df
        return pd.DataFrame()

    @staticmethod
    def get_live_whale_holders() -> pd.DataFrame:
        all_holders = []
        for ticker in WATCHLIST:
            try:
                stock = yf.Ticker(ticker)
                holders = stock.institutional_holders
                if holders is not None and not holders.empty:
                    top_whales = holders.head(2).copy()
                    for idx, row in top_whales.iterrows():
                        
                        pct_held = row.get("pctHeld", 0)
                        if pd.isna(pct_held): pct_held = 0
                        
                        pct_change = row.get("pctChange", 0)
                        if pd.isna(pct_change): pct_change = 0

                        val = row.get("Value", 0)
                        if pd.isna(val): val = 0

                        all_holders.append({
                            "Aktie (Ticker)": ticker,
                            "Unternehmen": TICKER_NAMES.get(ticker, ticker),
                            "Großaktionär (Fonds)": row.get("Holder", "Unknown"),
                            "Anteil am Unternehmen": f"{pct_held * 100:.2f} %",
                            "Veränderung (Quartal)": f"{pct_change * 100:+.2f} %",
                            "Aktien im Besitz": row.get("Shares", 0),
                            "Gesamtwert (USD)": f"${val:,.0f}",
                            "Stichtag": str(row.get("Date Reported", ""))[:10],
                        })
            except Exception as e:
                print(f"Error fetching whale data for {ticker}: {e}")
                
        if all_holders:
            return pd.DataFrame(all_holders)
        return pd.DataFrame()

class WhaleInsiderTracker(LiveInsiderWhaleTracker):
    @staticmethod
    def get_whale_sentiment_for_ticker(symbol: str) -> Dict[str, Any]:
        has_activity = False
        score_boost = 0
        whale_holders = []
        insider_buyers = []
        
        try:
            stock = yf.Ticker(symbol)
            holders = stock.institutional_holders
            if holders is not None and not holders.empty:
                for idx, row in holders.head(3).iterrows():
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
