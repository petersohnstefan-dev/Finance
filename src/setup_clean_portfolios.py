import json
import os
import datetime
from src.portfolio import PortfolioManager
from src.data_fetcher import FinancialDataFetcher

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolios.json")

def reset_and_populate():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    init_data = {
        "created_at": now_str,
        "currency": "EUR",
        "portfolios": {
            "short_term": {
                "name": "⚡ Kurz-/Mittelfristiges Trading-Depot (Aktien, Krypto & Momentum)",
                "strategy": "Aktives Swing-Trading auf Momentum, Ausbrüche & Short Squeezes mit Stop-Loss (-7%) und Take-Profit (+20%).",
                "initial_cash": 10000.0,
                "cash": 10000.0,
                "positions": {},
                "history": []
            },
            "long_term": {
                "name": "🏛️ Langfristiges Investment-Depot (Qualität, Gold & Krypto-Core)",
                "strategy": "Langfristiges Buy & Hold bei soliden Burggraben-Unternehmen (ROE > 15%), Gold zur Absicherung und Bitcoin als Core-Asset.",
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

    # 1. Short-Term Trading Depot
    short_allocations = [
        {"symbol": "MRNA", "alloc": 2000.0, "reason": "Biotech-Ausbruch, hoher Short Float (15.2%) und hohes Volumen"},
        {"symbol": "RIVN", "alloc": 2000.0, "reason": "Top Kurzfrist-Momentum (Score 95/100) über EMA 20/50"},
        {"symbol": "PLTR", "alloc": 2000.0, "reason": "Starker Foren-Buzz, hohes Kaufvolumen und KI-Wachstum"},
        {"symbol": "SOL-USD", "alloc": 1500.0, "reason": "High-Beta Krypto-Momentum mit bullischem MACD-Setup"},
        {"symbol": "DUOL", "alloc": 1500.0, "reason": "Trendfolge-Setup über 200-Tage-Linie mit stabiler Wachstumsdynamik"}
    ]

    for item in short_allocations:
        sym = item["symbol"]
        try:
            fetcher = FinancialDataFetcher(sym)
            fund = fetcher.get_fundamentals()
            p = fund.get("currentPrice") or 100.0
            shares = item["alloc"] / p
            sl = p * 0.93  # -7% Stop Loss
            tp = p * 1.20  # +20% Take Profit
            pm.buy("short_term", sym, fund.get("shortName", sym), shares, p, 
                   reason=item["reason"], stop_loss=sl, take_profit=tp)
            print(f"[Short-Term] Gekauft: {sym} ({shares:.2f} Stk. zu {p:.2f})")
        except Exception as e:
            print(f"Fehler bei {sym}: {e}")

    # 2. Long-Term Investment Depot
    long_allocations = [
        {"symbol": "SAP.DE", "alloc": 2000.0, "reason": "Europäischer Software-Monopolist, ROE 18.3%, solide Bilanz"},
        {"symbol": "MUV2.DE", "alloc": 2000.0, "reason": "Münchener Rück: KGV unter 10, starke Dividendenhistorie, Langfrist-Score 100"},
        {"symbol": "ADBE", "alloc": 2000.0, "reason": "Adobe: KGV ~15.7, hohe Free-Cashflow-Marge, weltweiter Software-Moat"},
        {"symbol": "GC=F", "alloc": 1500.0, "reason": "Gold: Makro-Wertspeicher & Inflationsschutz im übergeordneten Bullenmarkt"},
        {"symbol": "BTC-USD", "alloc": 1500.0, "reason": "Bitcoin: Digitales Gold, limitierte Geldmenge und langfristiger Makrotrend über SMA200"}
    ]

    for item in long_allocations:
        sym = item["symbol"]
        try:
            fetcher = FinancialDataFetcher(sym)
            fund = fetcher.get_fundamentals()
            p = fund.get("currentPrice") or 100.0
            shares = item["alloc"] / p
            pm.buy("long_term", sym, fund.get("shortName", sym), shares, p, 
                   reason=item["reason"])
            print(f"[Long-Term] Gekauft: {sym} ({shares:.2f} Stk. zu {p:.2f})")
        except Exception as e:
            print(f"Fehler bei {sym}: {e}")

    print("Depots erfolgreich bereinigt und mit Aktien, Gold & Krypto initialisiert!")

if __name__ == "__main__":
    reset_and_populate()
