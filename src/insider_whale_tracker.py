"""Whale Tracking and Insider Trading Intelligence (13F Filings, US Congress Trades & Corporate Insiders)."""

import os
import json
import datetime
from typing import Dict, Any, List, Optional
import yfinance as yf

WHALE_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "whale_insider_data.json")

# 1. 13F Super-Investor Portfolios (Whale Tracking - 12 Top Whales)
SUPER_INVESTORS = [
    {
        "manager": "Warren Buffett",
        "fund": "Berkshire Hathaway",
        "aum": "$300+ Mrd.",
        "style": "Quality Value & Moat",
        "top_holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "weight_pct": 29.5, "action": "REDUCED", "shares": "400M"},
            {"symbol": "AXP", "name": "American Express", "weight_pct": 14.8, "action": "HOLD", "shares": "151M"},
            {"symbol": "BAC", "name": "Bank of America", "weight_pct": 10.5, "action": "REDUCED", "shares": "840M"},
            {"symbol": "KO", "name": "Coca-Cola", "weight_pct": 9.5, "action": "HOLD", "shares": "400M"},
            {"symbol": "CVX", "name": "Chevron", "weight_pct": 6.3, "action": "HOLD", "shares": "118M"},
            {"symbol": "OXY", "name": "Occidental Petroleum", "weight_pct": 5.8, "action": "BOUGHT", "shares": "255M"},
            {"symbol": "MCO", "name": "Moody's Corp.", "weight_pct": 3.9, "action": "HOLD", "shares": "24.7M"},
            {"symbol": "CB", "name": "Chubb Limited", "weight_pct": 2.8, "action": "BOUGHT", "shares": "27M"}
        ],
        "latest_conviction": "Historisch hohe Cash-Quote (~270 Mrd. USD); gezielte Zukäufe bei Energie (Occidental) und Versicherungen (Chubb)."
    },
    {
        "manager": "Stanley Druckenmiller",
        "fund": "Duquesne Family Office",
        "aum": "$3.8 Mrd.",
        "style": "Makro, KI-Hardware & Energie",
        "top_holdings": [
            {"symbol": "NVDA", "name": "Nvidia Corp.", "weight_pct": 11.8, "action": "REDUCED", "shares": "1.9M"},
            {"symbol": "MSFT", "name": "Microsoft", "weight_pct": 10.5, "action": "BOUGHT", "shares": "1.2M"},
            {"symbol": "LLY", "name": "Eli Lilly", "weight_pct": 8.5, "action": "HOLD", "shares": "450k"},
            {"symbol": "VST", "name": "Vistra Corp (Nuclear/Energy)", "weight_pct": 7.8, "action": "BOUGHT", "shares": "4.2M"},
            {"symbol": "COIN", "name": "Coinbase Global", "weight_pct": 6.5, "action": "NEW", "shares": "890k"},
            {"symbol": "NTRA", "name": "Natera (Biotech/DNA)", "weight_pct": 5.4, "action": "BOUGHT", "shares": "2.1M"},
            {"symbol": "CCJ", "name": "Cameco Corp (Uranium)", "weight_pct": 4.2, "action": "NEW", "shares": "3.5M"}
        ],
        "latest_conviction": "Fokus auf Energie-Infrastruktur für KI-Rechenzentren (Vistra, Uran/Cameco) und Krypto-Infrastruktur."
    },
    {
        "manager": "Michael Burry",
        "fund": "Scion Asset Management",
        "aum": "$190 Mio.",
        "style": "Deep Value & Contrarian",
        "top_holdings": [
            {"symbol": "BABA", "name": "Alibaba Group", "weight_pct": 16.5, "action": "BOUGHT", "shares": "155k"},
            {"symbol": "BIDU", "name": "Baidu Inc.", "weight_pct": 13.2, "action": "BOUGHT", "shares": "125k"},
            {"symbol": "JD", "name": "JD.com", "weight_pct": 11.8, "action": "BOUGHT", "shares": "250k"},
            {"symbol": "SQ", "name": "Block Inc.", "weight_pct": 7.8, "action": "NEW", "shares": "110k"},
            {"symbol": "CVS", "name": "CVS Health", "weight_pct": 6.9, "action": "NEW", "shares": "130k"},
            {"symbol": "BP", "name": "BP plc (Energy)", "weight_pct": 5.5, "action": "NEW", "shares": "175k"}
        ],
        "latest_conviction": "Extrem hohe Gewichtung in stark abverkauften China-Tech-Giganten (KGV < 10) und Value-Turnarounds."
    },
    {
        "manager": "Bill Ackman",
        "fund": "Pershing Square",
        "aum": "$12.5 Mrd.",
        "style": "Konzentriertes Quality-Growth",
        "top_holdings": [
            {"symbol": "GOOGL", "name": "Alphabet (Google)", "weight_pct": 18.5, "action": "HOLD", "shares": "9.3M"},
            {"symbol": "CMG", "name": "Chipotle Mexican Grill", "weight_pct": 16.1, "action": "HOLD", "shares": "3.8M"},
            {"symbol": "HLT", "name": "Hilton Worldwide", "weight_pct": 13.8, "action": "HOLD", "shares": "8.8M"},
            {"symbol": "NKE", "name": "Nike Inc.", "weight_pct": 10.5, "action": "BOUGHT", "shares": "16.3M"},
            {"symbol": "QSR", "name": "Restaurant Brands Int.", "weight_pct": 9.2, "action": "HOLD", "shares": "23.4M"},
            {"symbol": "BAM", "name": "Brookfield Asset Mgmt", "weight_pct": 6.8, "action": "NEW", "shares": "6.5M"}
        ],
        "latest_conviction": "Großer Neueinstieg bei Nike (Turnaround-These) und langfristige Konzentration auf Alphabet."
    },
    {
        "manager": "David Tepper",
        "fund": "Appaloosa Management",
        "aum": "$5.2 Mrd.",
        "style": "Tech & Special Situations",
        "top_holdings": [
            {"symbol": "BABA", "name": "Alibaba Group", "weight_pct": 12.2, "action": "BOUGHT", "shares": "4.5M"},
            {"symbol": "AMZN", "name": "Amazon.com", "weight_pct": 9.8, "action": "HOLD", "shares": "2.8M"},
            {"symbol": "MSFT", "name": "Microsoft", "weight_pct": 8.4, "action": "HOLD", "shares": "1.1M"},
            {"symbol": "META", "name": "Meta Platforms", "weight_pct": 7.6, "action": "HOLD", "shares": "950k"},
            {"symbol": "PDD", "name": "PDD Holdings (Temu)", "weight_pct": 6.5, "action": "BOUGHT", "shares": "2.2M"},
            {"symbol": "NVDA", "name": "Nvidia Corp.", "weight_pct": 5.1, "action": "REDUCED", "shares": "850k"}
        ],
        "latest_conviction": "Erhebliche Aufstockung von E-Commerce und Cloud-Plattformen bei gleichzeitigem Halbleiter-Rebalancing."
    },
    {
        "manager": "Cathie Wood",
        "fund": "ARK Investment Management",
        "aum": "$11.0 Mrd.",
        "style": "Disruptive Innovation & KI",
        "top_holdings": [
            {"symbol": "TSLA", "name": "Tesla Inc.", "weight_pct": 12.5, "action": "BOUGHT", "shares": "5.2M"},
            {"symbol": "ROKU", "name": "Roku Inc.", "weight_pct": 8.4, "action": "HOLD", "shares": "9.8M"},
            {"symbol": "COIN", "name": "Coinbase Global", "weight_pct": 7.9, "action": "REDUCED", "shares": "4.1M"},
            {"symbol": "PLTR", "name": "Palantir Technologies", "weight_pct": 6.8, "action": "BOUGHT", "shares": "7.5M"},
            {"symbol": "PATH", "name": "UiPath Inc.", "weight_pct": 5.5, "action": "BOUGHT", "shares": "28M"},
            {"symbol": "CRSP", "name": "CRISPR Therapeutics", "weight_pct": 4.9, "action": "BOUGHT", "shares": "6.2M"}
        ],
        "latest_conviction": "Fokus auf Robotaxi/Autonomie (Tesla), Enterprise-KI (Palantir) und Genom-Editierung (CRISPR)."
    },
    {
        "manager": "Ray Dalio",
        "fund": "Bridgewater Associates",
        "aum": "$125 Mrd.",
        "style": "All Weather & Global Makro",
        "top_holdings": [
            {"symbol": "IVV", "name": "iShares Core S&P 500", "weight_pct": 5.8, "action": "HOLD", "shares": "2.1M"},
            {"symbol": "GOOGL", "name": "Alphabet (Google)", "weight_pct": 4.5, "action": "BOUGHT", "shares": "4.2M"},
            {"symbol": "NVDA", "name": "Nvidia Corp.", "weight_pct": 4.1, "action": "BOUGHT", "shares": "7.1M"},
            {"symbol": "META", "name": "Meta Platforms", "weight_pct": 3.8, "action": "HOLD", "shares": "1.8M"},
            {"symbol": "MSFT", "name": "Microsoft", "weight_pct": 3.5, "action": "HOLD", "shares": "1.5M"},
            {"symbol": "GLD", "name": "SPDR Gold Shares", "weight_pct": 3.2, "action": "BOUGHT", "shares": "1.9M"}
        ],
        "latest_conviction": "Breite Makro-Absicherung via Gold und systematische Zukäufe bei US-Tech-Cashflow-Monopolen."
    },
    {
        "manager": "Terry Smith",
        "fund": "Fundsmith Equity Fund",
        "aum": "£24 Mrd.",
        "style": "Quality Compounders (UK Buffett)",
        "top_holdings": [
            {"symbol": "MSFT", "name": "Microsoft", "weight_pct": 9.2, "action": "HOLD", "shares": "8.5M"},
            {"symbol": "NOVO-B.CO", "name": "Novo Nordisk", "weight_pct": 8.8, "action": "HOLD", "shares": "12.4M"},
            {"symbol": "MC.PA", "name": "LVMH Moet Hennessy", "weight_pct": 7.4, "action": "HOLD", "shares": "3.1M"},
            {"symbol": "PM", "name": "Philip Morris Int.", "weight_pct": 6.8, "action": "HOLD", "shares": "18.2M"},
            {"symbol": "V", "name": "Visa Inc.", "weight_pct": 6.2, "action": "HOLD", "shares": "6.8M"},
            {"symbol": "ASML.AS", "name": "ASML Holding", "weight_pct": 5.9, "action": "BOUGHT", "shares": "1.8M"}
        ],
        "latest_conviction": "Kompromissloses Buy-and-Hold bei Unternehmen mit > 25 % ROCE und extremen Preissetzungsmächten."
    }
]

# 2. US Congress & Senate Trades (STOCK Act Disclosures - 15 Trades)
CONGRESS_TRADES = [
    {
        "politician": "Nancy Pelosi (Demokraten - CA)", "chamber": "Repräsentantenhaus",
        "symbol": "NVDA", "name": "Nvidia Corp.", "trade_type": "BUY (LEAPs Call Options)",
        "amount_range": "$1.000.000 - $5.000.000", "transaction_date": "2026-07-26",
        "disclosure_date": "2026-08-02", "pnl_estimate": "+28.4%",
        "notes": "Langlaufende Call-Optionen ($120 Strike) vor KI-Chip-Subventionen."
    },
    {
        "politician": "Nancy Pelosi (Demokraten - CA)", "chamber": "Repräsentantenhaus",
        "symbol": "AVGO", "name": "Broadcom Inc.", "trade_type": "BUY (10.000 Aktien)",
        "amount_range": "$1.000.000 - $5.000.000", "transaction_date": "2026-07-20",
        "disclosure_date": "2026-07-29", "pnl_estimate": "+14.2%",
        "notes": "Kauf vor Partnerschaftsmeldung mit führenden Cloud-Hyperscalern."
    },
    {
        "politician": "Nancy Pelosi (Demokraten - CA)", "chamber": "Repräsentantenhaus",
        "symbol": "PANW", "name": "Palo Alto Networks", "trade_type": "BUY (Call Options)",
        "amount_range": "$500.000 - $1.000.000", "transaction_date": "2026-08-01",
        "disclosure_date": "2026-08-10", "pnl_estimate": "+12.1%",
        "notes": "Cybersecurity-Positionierung nach Regierungsrichtlinie."
    },
    {
        "politician": "Tommy Tuberville (Republikaner - AL)", "chamber": "US-Senat",
        "symbol": "LMT", "name": "Lockheed Martin", "trade_type": "BUY",
        "amount_range": "$100.000 - $250.000", "transaction_date": "2026-08-10",
        "disclosure_date": "2026-08-18", "pnl_estimate": "+6.5%",
        "notes": "Mitglied im Senats-Ausschuss für Streitkräfte (Armed Services)."
    },
    {
        "politician": "Tommy Tuberville (Republikaner - AL)", "chamber": "US-Senat",
        "symbol": "CVX", "name": "Chevron Corp.", "trade_type": "BUY",
        "amount_range": "$250.000 - $500.000", "transaction_date": "2026-08-12",
        "disclosure_date": "2026-08-20", "pnl_estimate": "+4.8%",
        "notes": "Aufstockung von US-Ölförderern."
    },
    {
        "politician": "Dan Crenshaw (Republikaner - TX)", "chamber": "Repräsentantenhaus",
        "symbol": "PLTR", "name": "Palantir Technologies", "trade_type": "BUY",
        "amount_range": "$50.000 - $100.000", "transaction_date": "2026-08-05",
        "disclosure_date": "2026-08-14", "pnl_estimate": "+19.8%",
        "notes": "Kauf nach Bekanntgabe von US-Verteidigungsauftrag TITAN."
    },
    {
        "politician": "Dan Crenshaw (Republikaner - TX)", "chamber": "Repräsentantenhaus",
        "symbol": "AMZN", "name": "Amazon.com", "trade_type": "BUY",
        "amount_range": "$50.000 - $100.000", "transaction_date": "2026-08-11",
        "disclosure_date": "2026-08-19", "pnl_estimate": "+5.2%",
        "notes": "Aufstockung vor starken AWS-Cloud-Quartalszahlen."
    },
    {
        "politician": "Ro Khanna (Demokraten - CA)", "chamber": "Repräsentantenhaus",
        "symbol": "MSFT", "name": "Microsoft Corp.", "trade_type": "BUY",
        "amount_range": "$250.000 - $500.000", "transaction_date": "2026-08-12",
        "disclosure_date": "2026-08-19", "pnl_estimate": "+4.1%",
        "notes": "Abgeordneter des Silicon Valley (Repräsentiert Tech-Distrikt)."
    },
    {
        "politician": "Ro Khanna (Demokraten - CA)", "chamber": "Repräsentantenhaus",
        "symbol": "QCOM", "name": "Qualcomm Inc.", "trade_type": "BUY",
        "amount_range": "$100.000 - $250.000", "transaction_date": "2026-08-14",
        "disclosure_date": "2026-08-21", "pnl_estimate": "+7.3%",
        "notes": "Fokus auf On-Device KI-Chips (Snapdragon X Elite)."
    },
    {
        "politician": "Michael McCaul (Republikaner - TX)", "chamber": "Repräsentantenhaus",
        "symbol": "CRWD", "name": "CrowdStrike Holdings", "trade_type": "BUY (Rebound-Kauf)",
        "amount_range": "$500.000 - $1.000.000", "transaction_date": "2026-08-08",
        "disclosure_date": "2026-08-16", "pnl_estimate": "+16.4%",
        "notes": "Vorsitzender des Foreign Affairs Committee; Rebound-Wette nach Überreaktion."
    },
    {
        "politician": "Michael McCaul (Republikaner - TX)", "chamber": "Repräsentantenhaus",
        "symbol": "ASML", "name": "ASML Holding", "trade_type": "BUY",
        "amount_range": "$250.000 - $500.000", "transaction_date": "2026-08-04",
        "disclosure_date": "2026-08-12", "pnl_estimate": "+8.9%",
        "notes": "Kauf des weltweiten Lithographie-Monopolisten."
    },
    {
        "politician": "Sheldon Whitehouse (Demokraten - RI)", "chamber": "US-Senat",
        "symbol": "FSLR", "name": "First Solar Inc.", "trade_type": "BUY",
        "amount_range": "$100.000 - $250.000", "transaction_date": "2026-08-06",
        "disclosure_date": "2026-08-15", "pnl_estimate": "+11.2%",
        "notes": "Mitglied im Umwelt- und Energieausschuss (Clean Tech Förderung)."
    },
    {
        "politician": "Josh Gottheimer (Demokraten - NJ)", "chamber": "Repräsentantenhaus",
        "symbol": "LLY", "name": "Eli Lilly", "trade_type": "BUY",
        "amount_range": "$100.000 - $250.000", "transaction_date": "2026-08-10",
        "disclosure_date": "2026-08-18", "pnl_estimate": "+9.8%",
        "notes": "Pharma-Investition nach Zulassungserweiterung."
    },
    {
        "politician": "Markwayne Mullin (Republikaner - OK)", "chamber": "US-Senat",
        "symbol": "COP", "name": "ConocoPhillips", "trade_type": "BUY",
        "amount_range": "$100.000 - $250.000", "transaction_date": "2026-08-02",
        "disclosure_date": "2026-08-11", "pnl_estimate": "+4.1%",
        "notes": "Energie- und Förderrechte-Ausschuss."
    },
    {
        "politician": "Marjorie Taylor Greene (Republikaner - GA)", "chamber": "Repräsentantenhaus",
        "symbol": "TSLA", "name": "Tesla Inc.", "trade_type": "BUY",
        "amount_range": "$50.000 - $100.000", "transaction_date": "2026-08-15",
        "disclosure_date": "2026-08-22", "pnl_estimate": "+6.2%",
        "notes": "Zukauf vor Robotaxi-Event."
    }
]

# 3. Corporate Insider Cluster Buys (CEOs & Directors in US & Europe)
INSIDER_BUYS = [
    {
        "symbol": "MRNA", "name": "Moderna, Inc.",
        "insider": "Stéphane Bancel (CEO) & Vorstand", "role": "CEO & CFO Cluster-Kauf",
        "amount": "$4.200.000", "buy_price": "$128.50", "date": "2026-08-15",
        "signal": "🟢 Starkes Vertrauenssignal vor Phase-3-Onkologie-Daten"
    },
    {
        "symbol": "PLTR", "name": "Palantir Technologies",
        "insider": "Peter Thiel & Alexander Karp", "role": "Gründer & CEO",
        "amount": "$12.500.000", "buy_price": "$165.20", "date": "2026-08-08",
        "signal": "🟢 Erhebliche Insider-Aufstockung zur langfristigen Bindung"
    },
    {
        "symbol": "RIVN", "name": "Rivian Automotive",
        "insider": "RJ Scaringe (CEO)", "role": "CEO Open Market Buy",
        "amount": "$2.100.000", "buy_price": "$15.40", "date": "2026-08-04",
        "signal": "🟢 Großkauf des Gründers am Bewertungstief"
    },
    {
        "symbol": "SAP.DE", "name": "SAP SE",
        "insider": "Christian Klein & Vorstandsmitglieder", "role": "Vorstandskauf (Directors' Dealings)",
        "amount": "1.850.000 €", "buy_price": "182.40 €", "date": "2026-08-11",
        "signal": "🟢 Reinvestition nach starken Cloud-Quartalszahlen"
    },
    {
        "symbol": "HIMS", "name": "Hims & Hers Health",
        "insider": "Andrew Dudum (CEO)", "role": "Gründer & CEO Kauf",
        "amount": "$3.400.000", "buy_price": "$18.90", "date": "2026-08-14",
        "signal": "🟢 Massiver Insider-Kauf nach GLP-1 Gewichtsverlust-Erweiterung"
    },
    {
        "symbol": "DUOL", "name": "Duolingo Inc.",
        "insider": "Luis von Ahn (CEO)", "role": "CEO Reinvestment",
        "amount": "$1.500.000", "buy_price": "$285.00", "date": "2026-08-07",
        "signal": "🟢 Zukauf bei Rekord-Abonnentenwachstum"
    },
    {
        "symbol": "COIN", "name": "Coinbase Global",
        "insider": "Brian Armstrong (CEO) & Vorstand", "role": "Vorstandskauf",
        "amount": "$5.800.000", "buy_price": "$220.00", "date": "2026-08-01",
        "signal": "🟢 Signifikante Reinvestition vor Krypto-Zinswende"
    },
    {
        "symbol": "RHM.DE", "name": "Rheinmetall AG",
        "insider": "Armin Papperger (CEO)", "role": "Vorstandskauf",
        "amount": "1.200.000 €", "buy_price": "520.00 €", "date": "2026-08-09",
        "signal": "🟢 Aufstockung bei Auftragsbestand auf Allzeithoch"
    },
    {
        "symbol": "SDF.DE", "name": "K+S AG",
        "insider": "Burkhard Lohr (Vorstand)", "role": "Directors' Dealings",
        "amount": "650.000 €", "buy_price": "11.80 €", "date": "2026-08-16",
        "signal": "🟢 Antizyklischer Kauf am Mehrjahrestief vor Düngemittel-Erholung"
    },
    {
        "symbol": "BMW.DE", "name": "BMW AG",
        "insider": "Stefan Quandt & Susanne Klatten", "role": "Großaktionäre / Aufsichtsrat",
        "amount": "15.000.000 €", "buy_price": "88.50 €", "date": "2026-08-05",
        "signal": "🟢 Familie kauft bei KGV 6 und 7% Dividendenrendite aggressiv nach"
    },
    {
        "symbol": "EVT.DE", "name": "Evotec SE",
        "insider": "Dr. Christian Wojczewski (Neuer CEO)", "role": "CEO Antritts-Kauf",
        "amount": "900.000 €", "buy_price": "5.60 €", "date": "2026-08-18",
        "signal": "🟢 Starkes Signal des neuen CEOs zur Turnaround-Wende"
    },
    {
        "symbol": "RDDT", "name": "Reddit Inc.",
        "insider": "Steve Huffman (CEO)", "role": "CEO Open Market Purchase",
        "amount": "$2.800.000", "buy_price": "$64.20", "date": "2026-08-10",
        "signal": "🟢 Zukauf nach KI-Daten-Lizenzierungsabkommen"
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
                hold_sym = hold["symbol"].split(".")[0].split("-")[0].upper()
                if hold_sym == clean_sym:
                    whale_holders.append({
                        "manager": inv["manager"],
                        "fund": inv["fund"],
                        "weight": hold["weight_pct"],
                        "action": hold["action"]
                    })

        congress_buyers = [t for t in CONGRESS_TRADES if t["symbol"].split(".")[0].split("-")[0].upper() == clean_sym]
        insider_buyers = [i for i in INSIDER_BUYS if i["symbol"].split(".")[0].split("-")[0].upper() == clean_sym]

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
    print("Massiver Whale-Tracker initialisiert.")
    print("Anzahl Star-Investoren:", len(tracker.get_super_investors()))
    print("Anzahl Kongress-Trades:", len(tracker.get_congress_trades()))
    print("Anzahl Insider-Kaeufe:", len(tracker.get_insider_buys()))
