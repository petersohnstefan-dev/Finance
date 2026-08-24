import json
import os
import datetime
from src.portfolio import PortfolioManager
from src.data_fetcher import FinancialDataFetcher

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolios.json")

def init_three_depots():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    init_data = {
        "created_at": now_str,
        "currency": "EUR",
        "portfolios": {
            "short_term": {
                "name": "⚡ Kurzfristiges Trading-Depot (Tage–Wochen / Squeezes & Hebel)",
                "strategy": "Aggressives Swing-Trading auf akute Ausbrüche, Short Squeezes & Krypto-Momentum via Hebel / Knock-Outs (Stop-Loss -7% / Take-Profit +20%).",
                "initial_cash": 10000.0,
                "cash": 10000.0,
                "positions": {},
                "history": []
            },
            "medium_term": {
                "name": "📈 Mittelfristiges Trend- & Growth-Depot (1–6 Monate / Swing)",
                "strategy": "Mittelfristige Trendfolge auf führende Wachstumsaktien & KI-Leader über der 50-Tage-Linie (Trailing Stop-Loss -10% / Take-Profit +35%).",
                "initial_cash": 10000.0,
                "cash": 10000.0,
                "positions": {},
                "history": []
            },
            "long_term": {
                "name": "🏛️ Langfristiges Investment-Depot (Jahre / Quality, Gold & Moat)",
                "strategy": "Klassisches Buy & Hold bei krisenfesten Burggraben-Unternehmen (ROE > 15%), Gold zur Absicherung, Bitcoin-Core und Bonus-Zertifikaten.",
                "initial_cash": 10000.0,
                "cash": 10000.0,
                "positions": {},
                "history": []
            }
        }
    }
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(init_data, f, indent=2, ensure_ascii=False)

    pm = PortfolioManager(initial_capital_per_depot=10000.0)

    # 1. Kurzfrist-Depot
    short_picks = [
        {"symbol": "MRNA", "alloc": 2000.0, "reason": "Akuter Biotech-Ausbruch & hoher Short Float (15.2%)", "sl_pct": 0.93, "tp_pct": 1.20},
        {"symbol": "RIVN", "alloc": 2000.0, "reason": "Top Kurzfrist-Momentum (95/100) & CEO-Insiderkauf", "sl_pct": 0.93, "tp_pct": 1.20},
        {"symbol": "SOL-USD", "alloc": 1500.0, "reason": "High-Beta Krypto-Momentum mit bullischem MACD-Setup", "sl_pct": 0.93, "tp_pct": 1.20}
    ]
    for p in short_picks:
        sym = p["symbol"]
        try:
            f = FinancialDataFetcher(sym)
            fund = f.get_fundamentals()
            px = fund.get("currentPrice") or 50.0
            shares = p["alloc"] / px
            pm.buy("short_term", sym, fund.get("shortName", sym), shares, px, 
                   reason=p["reason"], stop_loss=px * p["sl_pct"], take_profit=px * p["tp_pct"])
        except Exception as e:
            pass

    # 2. Mittelfrist-Depot
    medium_picks = [
        {"symbol": "PLTR", "alloc": 2000.0, "reason": "KI-Enterprise-Wachstum & Trendfolge über EMA 50", "sl_pct": 0.90, "tp_pct": 1.35},
        {"symbol": "DUOL", "alloc": 2000.0, "reason": "Stabiles Umsatzwachstum & Ausbruch über 200-Tage-Linie", "sl_pct": 0.90, "tp_pct": 1.35},
        {"symbol": "NVDA", "alloc": 2000.0, "reason": "KI-Hardware-Monopol & Nancy Pelosi Call-Optionen", "sl_pct": 0.90, "tp_pct": 1.35}
    ]
    for p in medium_picks:
        sym = p["symbol"]
        try:
            f = FinancialDataFetcher(sym)
            fund = f.get_fundamentals()
            px = fund.get("currentPrice") or 100.0
            shares = p["alloc"] / px
            pm.buy("medium_term", sym, fund.get("shortName", sym), shares, px, 
                   reason=p["reason"], stop_loss=px * p["sl_pct"], take_profit=px * p["tp_pct"])
        except Exception as e:
            pass

    # 3. Langfrist-Depot
    long_picks = [
        {"symbol": "SAP.DE", "alloc": 2000.0, "reason": "Europäischer Software-Monopolist, ROE 18.3%, solide Bilanz"},
        {"symbol": "MUV2.DE", "alloc": 2000.0, "reason": "Münchener Rück: KGV unter 10, exzellente Dividendenhistorie"},
        {"symbol": "GC=F", "alloc": 1500.0, "reason": "Gold: Makro-Wertspeicher & Inflationsschutz im Bullenmarkt"},
        {"symbol": "BTC-USD", "alloc": 1500.0, "reason": "Bitcoin: Digitales Gold & langfristiger Makrotrend über SMA200"}
    ]
    for p in long_picks:
        sym = p["symbol"]
        try:
            f = FinancialDataFetcher(sym)
            fund = f.get_fundamentals()
            px = fund.get("currentPrice") or 100.0
            shares = p["alloc"] / px
            pm.buy("long_term", sym, fund.get("shortName", sym), shares, px, 
                   reason=p["reason"])
        except Exception as e:
            pass

    print("Alle 3 Musterdepots (Kurz, Mittel, Lang) erfolgreich initialisiert.")

if __name__ == "__main__":
    init_three_depots()
