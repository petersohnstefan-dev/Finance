import codecs
import re

with codecs.open('src/insider_whale_tracker.py', 'r', 'utf8') as f:
    content = f.read()

# Replace get_live_insider_transactions
old_func = '''    def get_live_insider_transactions() -> pd.DataFrame:
        all_trades = []
        for ticker in WATCHLIST:
            try:
                stock = yf.Ticker(ticker)
                insiders = stock.insider_transactions
                if insiders is not None and not insiders.empty:
                    recent = insiders.head(3).copy()
                    for idx, row in recent.iterrows():
                        all_trades.append({
                            
                            "Aktie (Ticker)": ticker,
                            "Unternehmen": TICKER_NAMES.get(ticker, ticker),
                            "Insider / Person": str(row.get("Insider Purchases", row.get("Insider", "Unknown"))),
                            "Titel (Rolle)": str(row.get("Position", "-")),
                            "Details zur Transaktion": str(row.get("Text", "-")),
                            "Anzahl Aktien": row.get("Shares", 0),
                            "Transaktionswert ($)": row.get("Value", 0),
                            "Datum der SEC-Meldung": str(row.get("Start Date", row.get("Transaction Start Date", "")))[:10],
                        })
            except Exception as e:
                print(f"Error fetching insider data for {ticker}: {e}")
                
        if all_trades:
            import math
            df = pd.DataFrame(all_trades)
            
            def format_value(val):
                if isinstance(val, (int, float)) and not math.isnan(val) and val > 0:
                    return f"${val:,.2f}"
                return "$0.00"
            
            def format_text(txt):
                if isinstance(txt, str) and "0.00 per share" in txt:
                    return txt + " (Praktisch geschenkt erhalten!)"
                return txt
                
            if "Transaktionswert ($)" in df.columns:
                df["Transaktionswert ($)"] = df["Transaktionswert ($)"].apply(format_value)
            
            if "Details zur Transaktion" in df.columns:
                df["Details zur Transaktion"] = df["Details zur Transaktion"].apply(format_text)
                
            return df
        return pd.DataFrame()'''

new_func = '''    def get_live_insider_transactions() -> pd.DataFrame:
        all_trades = []
        for ticker in WATCHLIST:
            try:
                stock = yf.Ticker(ticker)
                insiders = stock.insider_transactions
                if insiders is not None and not insiders.empty:
                    # Filter out purely zero-value grants if we only want meaningful buys/sells
                    # but let's just show them and categorize them properly.
                    recent = insiders.head(5).copy()
                    for idx, row in recent.iterrows():
                        text = str(row.get("Text", "-"))
                        # Categorize
                        trade_type = "UNBEKANNT"
                        if "Purchase" in text or "Buy" in text:
                            trade_type = " KAUF"
                        elif "Sale" in text or "Sell" in text:
                            trade_type = " VERKAUF"
                        elif "Grant" in text or "Award" in text or "Gift" in text or "0.00 per share" in text:
                            trade_type = " ZUTEILUNG/GESCHENK"
                            
                        # Format Shares as integer
                        shares = row.get("Shares", 0)
                        
                        all_trades.append({
                            "Datum": str(row.get("Start Date", row.get("Transaction Start Date", "")))[:10],
                            "Aktie (Ticker)": ticker,
                            "Typ": trade_type,
                            "Insider / Person": str(row.get("Insider Purchases", row.get("Insider", "Unknown"))),
                            "Titel (Rolle)": str(row.get("Position", "-")),
                            "Anzahl Aktien": shares,
                            "Transaktionswert ($)": row.get("Value", 0),
                            "Details zur Transaktion": text
                        })
            except Exception as e:
                print(f"Error fetching insider data for {ticker}: {e}")
                
        if all_trades:
            import math
            df = pd.DataFrame(all_trades)
            
            def format_value(val):
                if isinstance(val, (int, float)) and not math.isnan(val) and val > 0:
                    return f"${val:,.0f}"  # Changed to whole numbers!
                return "$0"
                
            def format_shares(val):
                if isinstance(val, (int, float)) and not math.isnan(val):
                    return f"{val:,.0f}"  # Whole numbers
                return str(val)
            
            def format_text(txt):
                if isinstance(txt, str) and "0.00 per share" in txt:
                    return txt + " (Praktisch geschenkt erhalten!)"
                return txt
                
            if "Transaktionswert ($)" in df.columns:
                df["Transaktionswert ($)"] = df["Transaktionswert ($)"].apply(format_value)
                
            if "Anzahl Aktien" in df.columns:
                df["Anzahl Aktien"] = df["Anzahl Aktien"].apply(format_shares)
            
            if "Details zur Transaktion" in df.columns:
                df["Details zur Transaktion"] = df["Details zur Transaktion"].apply(format_text)
                
            return df
        return pd.DataFrame()'''

content = content.replace(old_func, new_func)

with codecs.open('src/insider_whale_tracker.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched insider_whale_tracker.py")
