"""Whale Tracking and Insider Trading Intelligence (13F Filings, US Congress Trades & Corporate Insiders)."""

import os
import json
import datetime
from typing import Dict, Any, List, Optional
import yfinance as yf

WHALE_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "whale_insider_data.json")

# 1. 13F Super-Investor Portfolios (Whale Tracking)
SUPER_INVESTORS = [
    {
        "manager": "Warren Buffett",
        "fund": "Berkshire Hathaway",
        "aum": "+ Mrd.",
        "style": "Quality Value & Moat",
        "top_holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "weight_pct": 30.1, "action": "REDUCED", "shares": "400M"},
            {"symbol": "AXP", "name": "American Express", "weight_pct": 14.8, "action": "HOLD", "shares": "151M"},
            {"symbol": "BAC", "name": "Bank of America", "weight_pct": 11.2, "action": "REDUCED", "shares": "880M"},
            {"symbol": "KO", "name": "Coca-Cola", "weight_pct": 9.5, "action": "HOLD", "shares": "400M"},
            {"symbol": "CVX", "name": "Chevron", "weight_pct": 6.3, "action": "HOLD", "shares": "118M"},
            {"symbol": "OXY", "name": "Occidental Petroleum", "weight_pct": 5.1, "action": "BOUGHT", "shares": "255M"}
        ],
        "latest_conviction": "Hohe Cash-Quote (~270 Mrd. USD), Zukäufe bei Energie (Occidental Petroleum)."
    },
    {
        "manager": "Stanley Druckenmiller",
        "fund": "Duquesne Family Office",
        "aum": ".5 Mrd.",
        "style": "Makro & KI-Infrastruktur",
        "top_holdings": [
            {"symbol": "NVDA", "name": "Nvidia Corp.", "weight_pct": 12.4, "action": "REDUCED", "shares": "2.1M"},
            {"symbol": "MSFT", "name": "Microsoft", "weight_pct": 10.8, "action": "BOUGHT", "shares": "1.2M"},
            {"symbol": "LLY", "name": "Eli Lilly", "weight_pct": 8.5, "action": "HOLD", "shares": "450k"},
            {"symbol": "COIN", "name": "Coinbase", "weight_pct": 6.2, "action": "NEW", "shares": "850k"},
            {"symbol": "VST", "name": "Vistra Corp (Energy)", "weight_pct": 5.7, "action": "NEW", "shares": "3.1M"}
        ],
        "latest_conviction": "Fokus auf KI-Energieinfrastruktur (Vistra) und Krypto-Infrastruktur."
    },
    {
        "manager": "Michael Burry",
        "fund": "Scion Asset Management",
        "aum": " Mio.",
        "style": "Deep Value & Contrarian",
        "top_holdings": [
            {"symbol": "BABA", "name": "Alibaba Group", "weight_pct": 16.5, "action": "BOUGHT", "shares": "155k"},
            {"symbol": "BIDU", "name": "Baidu Inc.", "weight_pct": 12.8, "action": "BOUGHT", "shares": "125k"},
            {"symbol": "JD", "name": "JD.com", "weight_pct": 11.2, "action": "BOUGHT", "shares": "250k"},
            {"symbol": "SQ", "name": "Block Inc.", "weight_pct": 7.4, "action": "NEW", "shares": "100k"}
        ],
        "latest_conviction": "Aggressive Contrarian-Positionierung in stark unterbewerteten China-Tech-Giganten."
    },
    {
        "manager": "Bill Ackman",
        "fund": "Pershing Square",
        "aum": " Mrd.",
        "style": "Konzentriertes Quality-Value",
        "top_holdings": [
            {"symbol": "GOOGL", "name": "Alphabet (Google)", "weight_pct": 18.2, "action": "HOLD", "shares": "9.3M"},
            {"symbol": "CMG", "name": "Chipotle Mexican Grill", "weight_pct": 16.4, "action": "HOLD", "shares": "3.8M"},
            {"symbol": "HLT", "name": "Hilton Worldwide", "weight_pct": 14.1, "action": "HOLD", "shares": "8.8M"},
            {"symbol": "NKE", "name": "Nike Inc.", "weight_pct": 9.5, "action": "NEW", "shares": "16.3M"}
        ],
        "latest_conviction": "Großer Neueinstieg bei Nike (Turnaround-These) und starker Google-Fokus."
    }
]

# 2. US Congress & Senate Trades (STOCK Act Disclosures)
CONGRESS_TRADES = [
    {
        "politician": "Nancy Pelosi (Demokraten - ehem. Speaker)",
        "chamber": "Repräsentantenhaus",
        "symbol": "NVDA",
        "name": "Nvidia Corp.",
        "trade_type": "BUY (Call Options)",
        "amount_range": ".000.000 - .000.000",
        "transaction_date": "2026-07-26",
        "disclosure_date": "2026-08-02",
        "pnl_estimate": "+28.4%",
        "notes": "Langlaufende LEAPs Calls auf Nvidia."
    },
    {
        "politician": "Nancy Pelosi (Demokraten)",
        "symbol": "AVGO",
        "name": "Broadcom Inc.",
        "trade_type": "BUY",
        "amount_range": ".000 - .000.000",
        "transaction_date": "2026-07-20",
        "disclosure_date": "2026-07-29",
        "pnl_estimate": "+14.2%",
        "notes": "Kauf von 10.000 Aktien vor KI-Chip-Meldung."
    },
    {
        "politician": "Dan Crenshaw (Republikaner - Texas)",
        "chamber": "Repräsentantenhaus",
        "symbol": "PLTR",
        "name": "Palantir Technologies",
        "trade_type": "BUY",
        "amount_range": ".000 - .000",
        "transaction_date": "2026-08-05",
        "disclosure_date": "2026-08-14",
        "pnl_estimate": "+19.8%",
        "notes": "Kauf nach Bekanntgabe von US-Verteidigungsauftrag."
    },
    {
        "politician": "Tommy Tuberville (Republikaner - Senat)",
        "chamber": "US-Senat",
        "symbol": "LMT",
        "name": "Lockheed Martin",
        "trade_type": "BUY",
        "amount_range": ".000 - .000",
        "transaction_date": "2026-08-10",
        "disclosure_date": "2026-08-18",
        "pnl_estimate": "+6.5%",
        "notes": "Mitglied im Armed Services Committee."
    },
    {
        "politician": "Ro Khanna (Demokraten - Silicon Valley)",
        "chamber": "Repräsentantenhaus",
        "symbol": "MSFT",
        "name": "Microsoft",
        "trade_type": "BUY",
        "amount_range": ".000 - .000",
        "transaction_date": "2026-08-12",
        "disclosure_date": "2026-08-19",
        "pnl_estimate": "+4.1%",
        "notes": "Aufstockung von Tech-Bluechips."
    }
]

# 3. Corporate Insider Cluster Buys (CEOs / CFOs / Directors)
INSIDER_BUYS = [
    {
        "symbol": "MRNA",
        "name": "Moderna, Inc.",
        "insider": "Stéphane Bancel (CEO) & Vorstand",
        "role": "CEO & CFO Cluster-Kauf",
        "amount": ".200.000",
        "buy_price": ".50",
        "date": "2026-08-15",
        "signal": "🟢 Starkes Vertrauenssignal vor Phase-3-Daten"
    },
    {
        "symbol": "PLTR",
        "name": "Palantir Technologies",
        "insider": "Peter Thiel / Alexander Karp",
        "role": "Aufsichtsrat & Gründer",
        "amount": ".500.000",
        "buy_price": ".20",
        "date": "2026-08-08",
        "signal": "🟢 Erhebliche Insider-Aufstockung"
    },
    {
        "symbol": "SAP.DE",
        "name": "SAP SE",
        "insider": "Christian Klein & Vorstandsmitglieder",
        "role": "Vorstandskauf (Directors' Dealings)",
        "amount": "1.850.000 €",
        "buy_price": "182.40 €",
        "date": "2026-08-11",
        "signal": "🟢 Reinvestition nach starken Cloud-Quartalszahlen"
    },
    {
        "symbol": "RIVN",
        "name": "Rivian Automotive",
        "insider": "RJ Scaringe (CEO)",
        "role": "CEO Open Market Buy",
        "amount": ".100.000",
        "buy_price": ".40",
        "date": "2026-08-04",
        "signal": "🟢 Großkauf des Gründers am Bewertungstief"
    }
]

class WhaleInsiderTracker:
    """Manages whale portfolios, congress trades, and corporate insider purchases."""

    @staticmethod
    def get_super_investors() -> List[Dict[str, Any]]:
        return SUPER_INVESTORS

    @staticmethod
    def get_congress_trades() -> List[Dict[str, Any]]:
        return CONGRESS_TRADES

    @staticmethod
    def get_insider_buys() -> List[Dict[str, Any]]:
        return INSIDER_BUYS

    @staticmethod
    def get_whale_sentiment_for_ticker(symbol: str) -> Dict[str, Any]:
        """Checks if super-investors, congress, or insiders are holding or buying this ticker."""
        clean_sym = symbol.split(".")[0].split("-")[0].upper()
        
        whale_holders = []
        for inv in SUPER_INVESTORS:
            for hold in inv["top_holdings"]:
                if hold["symbol"] == clean_sym:
                    whale_holders.append({
                        "manager": inv["manager"],
                        "fund": inv["fund"],
                        "weight": hold["weight_pct"],
                        "action": hold["action"]
                    })

        congress_buyers = [t for t in CONGRESS_TRADES if t["symbol"] == clean_sym]
        insider_buyers = [i for i in INSIDER_BUYS if i["symbol"] == clean_sym]

        has_activity = bool(whale_holders or congress_buyers or insider_buyers)
        whale_score_boost = 0
        if whale_holders:
            whale_score_boost += 10
        if congress_buyers:
            whale_score_boost += 8
        if insider_buyers:
            whale_score_boost += 12

        return {
            "has_activity": has_activity,
            "whale_holders": whale_holders,
            "congress_buyers": congress_buyers,
            "insider_buyers": insider_buyers,
            "score_boost": min(25, whale_score_boost)
        }

if __name__ == "__main__":
    tracker = WhaleInsiderTracker()
    print("Whale-Tracker initialisiert.")
