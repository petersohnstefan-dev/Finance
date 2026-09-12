import codecs
import re

with codecs.open('src/insider_whale_tracker.py', 'r', 'utf8') as f:
    content = f.read()

new_func = '''    def get_live_insider_transactions() -> pd.DataFrame:
        all_trades = []
        for ticker in WATCHLIST:
            try:
                stock = yf.Ticker(ticker)
                insiders = stock.insider_transactions
                if insiders is not None and not insiders.empty:
                    recent = insiders.head(5).copy()
                    for idx, row in recent.iterrows():
                        text = str(row.get("Text", "-"))
                        
                        trade_type = "UNBEKANNT"
                        if "Purchase" in text or "Buy" in text:
                            trade_type = " KAUF"
                        elif "Sale" in text or "Sell" in text:
                            trade_type = " VERKAUF"
                        elif "Grant" in text or "Award" in text or "Gift" in text or "0.00 per share" in text:
                            trade_type = " ZUTEILUNG (GESCHENK)"
                            
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
        return pd.DataFrame()'''

# Replace the method using regex
content = re.sub(r'    def get_live_insider_transactions\(\) -> pd\.DataFrame:.*?return pd\.DataFrame\(\)', new_func, content, flags=re.DOTALL)

with codecs.open('src/insider_whale_tracker.py', 'w', 'utf8') as f:
    f.write(content)
print("Regex patch successful")
