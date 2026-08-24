import json
import os
from src.portfolio import PortfolioManager
from src.data_fetcher import FinancialDataFetcher

def setup_depots():
    pm = PortfolioManager(initial_capital_per_depot=10000.0)
    
    # 1. Short-Term Trading Depot
    short_picks = [
        {"symbol": "MRNA", "alloc": 2000.0, "reason": "Ausbruchs-Dynamik, hoher Leerverkaeufer-Float (15.2%) und Rebound-Potenzial"},
        {"symbol": "RIVN", "alloc": 2000.0, "reason": "Top Kurzfrist-Score (95/100) und dynamisches Chart-Momentum"},
        {"symbol": "PLTR", "alloc": 2000.0, "reason": "Starker Foren-Buzz, hohes Kaufvolumen und KI-Wachstum"},
        {"symbol": "DUOL", "alloc": 2000.0, "reason": "Ausbruchs-Score 40, starkes Momentum ueber EMA 20 & 50"}
    ]
    
    for pick in short_picks:
        sym = pick["symbol"]
        try:
            fetcher = FinancialDataFetcher(sym)
            fund = fetcher.get_fundamentals()
            p = fund.get("currentPrice") or 50.0
            shares = pick["alloc"] / p
            sl = p * 0.93  # -7% Stop Loss
            tp = p * 1.20  # +20% Take Profit
            pm.buy("short_term", sym, fund.get("shortName", sym), shares, p, 
                   reason=pick["reason"], stop_loss=sl, take_profit=tp)
            print(f"[Kurzfrist-Depot] Gekauft: {sym} ({shares:.2f} Stk. zu {p:.2f})")
        except Exception as e:
            print(f"Fehler bei {sym}: {e}")

    # 2. Long-Term Investment Depot
    long_picks = [
        {"symbol": "SAP.DE", "alloc": 2000.0, "reason": "Europaeischer Software-Monopolist, ROE 18.3%, solide Bilanz (Debt/Equity 0.22)"},
        {"symbol": "MUV2.DE", "alloc": 2000.0, "reason": "Muenchener Rueck: KGV unter 10, exzellente Dividendenhistorie, Langfrist-Score 100"},
        {"symbol": "ADBE", "alloc": 2000.0, "reason": "Adobe: KGV ~15.7, hohe Free-Cashflow-Marge, weltweiter Software-Burggraben"},
        {"symbol": "CAP.PA", "alloc": 2000.0, "reason": "Capgemini: Attraktives KGV 14.0, starkes IT-Wachstum, solides Rating"}
    ]

    for pick in long_picks:
        sym = pick["symbol"]
        try:
            fetcher = FinancialDataFetcher(sym)
            fund = fetcher.get_fundamentals()
            p = fund.get("currentPrice") or 100.0
            shares = pick["alloc"] / p
            pm.buy("long_term", sym, fund.get("shortName", sym), shares, p, 
                   reason=pick["reason"])
            print(f"[Langfrist-Depot] Gekauft: {sym} ({shares:.2f} Stk. zu {p:.2f})")
        except Exception as e:
            print(f"Fehler bei {sym}: {e}")

    print("Beide Musterdepots mit je 10.000 EUR Startkapital erfolgreich eingerichtet!")

if __name__ == "__main__":
    setup_depots()
