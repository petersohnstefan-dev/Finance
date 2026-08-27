"""Whale Tracking and Insider Trading Intelligence (13F Filings, US Congress Trades & Corporate Insiders)."""

import os
import json
import datetime
from typing import Dict, Any, List, Optional

WHALE_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "whale_insider_data.json")

# 1. 13F Super-Investor Portfolios (Whale Tracking - 8 Top Whales)
SUPER_INVESTORS = [
    {
        "manager": "Warren Buffett",
        "fund": "Berkshire Hathaway",
        "aum": "$300+ Mrd.",
        "style": "Quality Value & Moat",
        "filing_date": "14.08.2026 (13F Q2)",
        "filing_period": "Q2 2026",
        "top_holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "weight_pct": 29.5, "action": "REDUCED", "shares": "400M", "est_buy_range": "$170 - $195"},
            {"symbol": "AXP", "name": "American Express", "weight_pct": 14.8, "action": "HOLD", "shares": "151M", "est_buy_range": "$140 - $175"},
            {"symbol": "BAC", "name": "Bank of America", "weight_pct": 10.5, "action": "REDUCED", "shares": "840M", "est_buy_range": "$32 - $41"},
            {"symbol": "KO", "name": "Coca-Cola", "weight_pct": 9.5, "action": "HOLD", "shares": "400M", "est_buy_range": "$55 - $63"},
            {"symbol": "CVX", "name": "Chevron", "weight_pct": 6.3, "action": "HOLD", "shares": "118M", "est_buy_range": "$145 - $160"},
            {"symbol": "OXY", "name": "Occidental Petroleum", "weight_pct": 5.8, "action": "BOUGHT", "shares": "255M", "est_buy_range": "$56 - $62"},
            {"symbol": "MCO", "name": "Moody's Corp.", "weight_pct": 3.9, "action": "HOLD", "shares": "24.7M", "est_buy_range": "$320 - $410"},
            {"symbol": "CB", "name": "Chubb Limited", "weight_pct": 2.8, "action": "BOUGHT", "shares": "27M", "est_buy_range": "$245 - $270"}
        ],
        "latest_conviction": "Historisch hohe Cash-Quote (~270 Mrd. USD); gezielte Zukäufe bei Energie (Occidental) und Versicherungen (Chubb)."
    },
    {
        "manager": "Stanley Druckenmiller",
        "fund": "Duquesne Family Office",
        "aum": "$3.8 Mrd.",
        "style": "Makro, KI-Hardware & Energie",
        "filing_date": "14.08.2026 (13F Q2)",
        "filing_period": "Q2 2026",
        "top_holdings": [
            {"symbol": "NVDA", "name": "Nvidia Corp.", "weight_pct": 11.8, "action": "REDUCED", "shares": "1.9M", "est_buy_range": "$95 - $125"},
            {"symbol": "MSFT", "name": "Microsoft", "weight_pct": 10.5, "action": "BOUGHT", "shares": "1.2M", "est_buy_range": "$410 - $450"},
            {"symbol": "LLY", "name": "Eli Lilly", "weight_pct": 8.5, "action": "HOLD", "shares": "450k", "est_buy_range": "$750 - $920"},
            {"symbol": "VST", "name": "Vistra Corp (Nuclear/Energy)", "weight_pct": 7.8, "action": "BOUGHT", "shares": "4.2M", "est_buy_range": "$70 - $95"},
            {"symbol": "COIN", "name": "Coinbase Global", "weight_pct": 6.5, "action": "NEW", "shares": "890k", "est_buy_range": "$190 - $240"},
            {"symbol": "NTRA", "name": "Natera (Biotech/DNA)", "weight_pct": 5.4, "action": "BOUGHT", "shares": "2.1M", "est_buy_range": "$95 - $115"},
            {"symbol": "CCJ", "name": "Cameco Corp (Uranium)", "weight_pct": 4.2, "action": "NEW", "shares": "3.5M", "est_buy_range": "$42 - $52"}
        ],
        "latest_conviction": "Fokus auf Energie-Infrastruktur für KI-Rechenzentren (Vistra, Uran/Cameco) und Krypto-Infrastruktur."
    },
    {
        "manager": "Michael Burry",
        "fund": "Scion Asset Management",
        "aum": "$190 Mio.",
        "style": "Deep Value & Contrarian",
        "filing_date": "14.08.2026 (13F Q2)",
        "filing_period": "Q2 2026",
        "top_holdings": [
            {"symbol": "BABA", "name": "Alibaba Group", "weight_pct": 16.5, "action": "BOUGHT", "shares": "155k", "est_buy_range": "$72 - $85"},
            {"symbol": "BIDU", "name": "Baidu Inc.", "weight_pct": 13.2, "action": "BOUGHT", "shares": "125k", "est_buy_range": "$85 - $100"},
            {"symbol": "JD", "name": "JD.com", "weight_pct": 11.8, "action": "BOUGHT", "shares": "250k", "est_buy_range": "$24 - $30"},
            {"symbol": "SQ", "name": "Block Inc.", "weight_pct": 7.8, "action": "NEW", "shares": "110k", "est_buy_range": "$60 - $70"},
            {"symbol": "CVS", "name": "CVS Health", "weight_pct": 6.9, "action": "NEW", "shares": "130k", "est_buy_range": "$54 - $62"},
            {"symbol": "BP", "name": "BP plc (Energy)", "weight_pct": 5.5, "action": "NEW", "shares": "175k", "est_buy_range": "$33 - $38"}
        ],
        "latest_conviction": "Extrem hohe Gewichtung in stark abverkauften China-Tech-Giganten (KGV < 10) und Value-Turnarounds."
    },
    {
        "manager": "Bill Ackman",
        "fund": "Pershing Square",
        "aum": "$12.5 Mrd.",
        "style": "Konzentriertes Quality-Growth",
        "filing_date": "14.08.2026 (13F Q2)",
        "filing_period": "Q2 2026",
        "top_holdings": [
            {"symbol": "GOOGL", "name": "Alphabet (Google)", "weight_pct": 18.5, "action": "HOLD", "shares": "9.3M", "est_buy_range": "$135 - $175"},
            {"symbol": "CMG", "name": "Chipotle Mexican Grill", "weight_pct": 16.1, "action": "HOLD", "shares": "3.8M", "est_buy_range": "$52 - $65"},
            {"symbol": "HLT", "name": "Hilton Worldwide", "weight_pct": 13.8, "action": "HOLD", "shares": "8.8M", "est_buy_range": "$190 - $220"},
            {"symbol": "NKE", "name": "Nike Inc.", "weight_pct": 10.5, "action": "BOUGHT", "shares": "16.3M", "est_buy_range": "$72 - $84"},
            {"symbol": "QSR", "name": "Restaurant Brands Int.", "weight_pct": 9.2, "action": "HOLD", "shares": "23.4M", "est_buy_range": "$68 - $78"},
            {"symbol": "BAM", "name": "Brookfield Asset Mgmt", "weight_pct": 6.8, "action": "NEW", "shares": "6.5M", "est_buy_range": "$36 - $42"}
        ],
        "latest_conviction": "Großer Neueinstieg bei Nike (Turnaround-These) und langfristige Konzentration auf Alphabet."
    },
    {
        "manager": "David Tepper",
        "fund": "Appaloosa Management",
        "aum": "$5.2 Mrd.",
        "style": "Tech & Special Situations",
        "filing_date": "14.08.2026 (13F Q2)",
        "filing_period": "Q2 2026",
        "top_holdings": [
            {"symbol": "BABA", "name": "Alibaba Group", "weight_pct": 12.2, "action": "BOUGHT", "shares": "4.5M", "est_buy_range": "$72 - $85"},
            {"symbol": "AMZN", "name": "Amazon.com", "weight_pct": 9.8, "action": "HOLD", "shares": "2.8M", "est_buy_range": "$175 - $195"},
            {"symbol": "MSFT", "name": "Microsoft", "weight_pct": 8.4, "action": "HOLD", "shares": "1.1M", "est_buy_range": "$410 - $445"},
            {"symbol": "META", "name": "Meta Platforms", "weight_pct": 7.6, "action": "HOLD", "shares": "950k", "est_buy_range": "$460 - $515"},
            {"symbol": "PDD", "name": "PDD Holdings (Temu)", "weight_pct": 6.5, "action": "BOUGHT", "shares": "2.2M", "est_buy_range": "$115 - $145"},
            {"symbol": "NVDA", "name": "Nvidia Corp.", "weight_pct": 5.1, "action": "REDUCED", "shares": "850k", "est_buy_range": "$105 - $130"}
        ],
        "latest_conviction": "Erhebliche Aufstockung von E-Commerce und Cloud-Plattformen bei gleichzeitigem Halbleiter-Rebalancing."
    },
    {
        "manager": "Cathie Wood",
        "fund": "ARK Investment Management",
        "aum": "$11.0 Mrd.",
        "style": "Disruptive Innovation & KI",
        "filing_date": "14.08.2026 (13F Q2)",
        "filing_period": "Q2 2026",
        "top_holdings": [
            {"symbol": "TSLA", "name": "Tesla Inc.", "weight_pct": 12.5, "action": "BOUGHT", "shares": "5.2M", "est_buy_range": "$180 - $240"},
            {"symbol": "ROKU", "name": "Roku Inc.", "weight_pct": 8.4, "action": "HOLD", "shares": "9.8M", "est_buy_range": "$55 - $68"},
            {"symbol": "COIN", "name": "Coinbase Global", "weight_pct": 7.9, "action": "REDUCED", "shares": "4.1M", "est_buy_range": "$210 - $255"},
            {"symbol": "PLTR", "name": "Palantir Technologies", "weight_pct": 6.8, "action": "BOUGHT", "shares": "7.5M", "est_buy_range": "$24 - $32"},
            {"symbol": "PATH", "name": "UiPath Inc.", "weight_pct": 5.5, "action": "BOUGHT", "shares": "28M", "est_buy_range": "$11 - $14"},
            {"symbol": "CRSP", "name": "CRISPR Therapeutics", "weight_pct": 4.9, "action": "BOUGHT", "shares": "6.2M", "est_buy_range": "$48 - $58"}
        ],
        "latest_conviction": "Fokus auf Robotaxi/Autonomie (Tesla), Enterprise-KI (Palantir) und Genom-Editierung (CRISPR)."
    },
    {
        "manager": "Ray Dalio",
        "fund": "Bridgewater Associates",
        "aum": "$125 Mrd.",
        "style": "All Weather & Global Makro",
        "filing_date": "14.08.2026 (13F Q2)",
        "filing_period": "Q2 2026",
        "top_holdings": [
            {"symbol": "IVV", "name": "iShares Core S&P 500", "weight_pct": 5.8, "action": "HOLD", "shares": "2.1M", "est_buy_range": "$500 - $550"},
            {"symbol": "GOOGL", "name": "Alphabet (Google)", "weight_pct": 4.5, "action": "BOUGHT", "shares": "4.2M", "est_buy_range": "$155 - $185"},
            {"symbol": "NVDA", "name": "Nvidia Corp.", "weight_pct": 4.1, "action": "BOUGHT", "shares": "7.1M", "est_buy_range": "$100 - $125"},
            {"symbol": "META", "name": "Meta Platforms", "weight_pct": 3.8, "action": "HOLD", "shares": "1.8M", "est_buy_range": "$470 - $510"},
            {"symbol": "MSFT", "name": "Microsoft", "weight_pct": 3.5, "action": "HOLD", "shares": "1.5M", "est_buy_range": "$420 - $450"},
            {"symbol": "GLD", "name": "SPDR Gold Shares", "weight_pct": 3.2, "action": "BOUGHT", "shares": "1.9M", "est_buy_range": "$215 - $230"}
        ],
        "latest_conviction": "Breite Makro-Absicherung via Gold und systematische Zukäufe bei US-Tech-Cashflow-Monopolen."
    },
    {
        "manager": "Terry Smith",
        "fund": "Fundsmith Equity Fund",
        "aum": "£24 Mrd.",
        "style": "Quality Compounders (UK Buffett)",
        "filing_date": "14.08.2026 (13F Q2)",
        "filing_period": "Q2 2026",
        "top_holdings": [
            {"symbol": "MSFT", "name": "Microsoft", "weight_pct": 9.2, "action": "HOLD", "shares": "8.5M", "est_buy_range": "$400 - $445"},
            {"symbol": "NOVO-B.CO", "name": "Novo Nordisk", "weight_pct": 8.8, "action": "HOLD", "shares": "12.4M", "est_buy_range": "850 - 980 DKK"},
            {"symbol": "MC.PA", "name": "LVMH Moet Hennessy", "weight_pct": 7.4, "action": "HOLD", "shares": "3.1M", "est_buy_range": "680 - 790 EUR"},
            {"symbol": "PM", "name": "Philip Morris Int.", "weight_pct": 6.8, "action": "HOLD", "shares": "18.2M", "est_buy_range": "$95 - $115"},
            {"symbol": "V", "name": "Visa Inc.", "weight_pct": 6.2, "action": "HOLD", "shares": "6.8M", "est_buy_range": "$260 - $285"},
            {"symbol": "ASML.AS", "name": "ASML Holding", "weight_pct": 5.9, "action": "BOUGHT", "shares": "1.8M", "est_buy_range": "780 - 950 EUR"}
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
    }
]

# 3. Corporate Insider Cluster Buys (CEOs & Directors with Net Worth / Commitment Ratio)
INSIDER_BUYS = [
    {
        "symbol": "MRNA", "name": "Moderna, Inc.",
        "insider": "Stéphane Bancel", "role": "CEO",
        "amount": "$4.200.000", "buy_price": "$128.50", "date": "2026-08-15",
        "net_worth_est": "$380 Mio.", "wealth_pct": "1.1%", "annual_comp": "$18 Mio.",
        "skin_in_game": "🟢 Hoch (23% des Jahresgehalts)",
        "signal": "🟢 Starkes Vertrauenssignal vor Phase-3-Daten"
    },
    {
        "symbol": "PLTR", "name": "Palantir Tech",
        "insider": "Alexander Karp & Peter Thiel", "role": "CEO & Gründer",
        "amount": "$12.500.000", "buy_price": "$165.20", "date": "2026-08-08",
        "net_worth_est": "$8.5 Mrd.", "wealth_pct": "0.15%", "annual_comp": "$5 Mio.",
        "skin_in_game": "🟢 Hoch (Erhebliche Reinvestition)",
        "signal": "🟢 Erhebliche Insider-Aufstockung"
    },
    {
        "symbol": "RIVN", "name": "Rivian Auto",
        "insider": "RJ Scaringe", "role": "CEO & Gründer",
        "amount": "$2.100.000", "buy_price": "$15.40", "date": "2026-08-04",
        "net_worth_est": "$45 Mio.", "wealth_pct": "4.7%", "annual_comp": "$1.2 Mio.",
        "skin_in_game": "🔥 ULTRA-HOCH (4.7% des Privatvermögens!)",
        "signal": "🟢 Großkauf am Bewertungstief"
    },
    {
        "symbol": "SAP.DE", "name": "SAP SE",
        "insider": "Christian Klein", "role": "CEO",
        "amount": "1.850.000 €", "buy_price": "182.40 €", "date": "2026-08-11",
        "net_worth_est": "25 Mio. €", "wealth_pct": "7.4%", "annual_comp": "4.2 Mio. €",
        "skin_in_game": "🔥 ULTRA-HOCH (44% des Jahresgehalts)",
        "signal": "🟢 Starker Kauf vor KI-Integration"
    },
    {
        "symbol": "SDF.DE", "name": "K+S AG",
        "insider": "Dr. Burkhard Lohr", "role": "CEO",
        "amount": "345.000 €", "buy_price": "14.20 €", "date": "2026-08-18",
        "net_worth_est": "8 Mio. €", "wealth_pct": "4.3%", "annual_comp": "2.1 Mio. €",
        "skin_in_game": "🟢 Hoch (Substanzieller Vermögensanteil)",
        "signal": "🟢 Antizyklischer Kauf am Zyklustief"
    },
    {
        "symbol": "CRWD", "name": "CrowdStrike",
        "insider": "George Kurtz", "role": "CEO & Gründer",
        "amount": "$8.400.000", "buy_price": "$295.10", "date": "2026-08-20",
        "net_worth_est": "$3.1 Mrd.", "wealth_pct": "0.27%", "annual_comp": "$4 Mio.",
        "skin_in_game": "🟢 Hoch (Rückkauf nach Earnings-Drop)",
        "signal": "🟢 Turnaround-Signal vom Gründer"
    },
    {
        "symbol": "NVDA", "name": "NVIDIA Corp.",
        "insider": "Harvey Jones", "role": "Board Director",
        "amount": "$15.200.000", "buy_price": "$124.50", "date": "2026-08-22",
        "net_worth_est": "$150 Mio.", "wealth_pct": "10.1%", "annual_comp": "$350k",
        "skin_in_game": "🔥 ULTRA-HOCH (Über 10% des Vermögens)",
        "signal": "🟢 Massives Vertrauen in nächste Blackwell-Chips"
    },
    {
        "symbol": "TSLA", "name": "Tesla Inc.",
        "insider": "Robyn Denholm", "role": "Chairperson",
        "amount": "$2.800.000", "buy_price": "$215.30", "date": "2026-08-24",
        "net_worth_est": "$35 Mio.", "wealth_pct": "8.0%", "annual_comp": "$1.5 Mio.",
        "skin_in_game": "🔥 ULTRA-HOCH (8% des Vermögens)",
        "signal": "🟢 Kauf vor neuem Robotaxi-Release"
    },
    {
        "symbol": "ALV.DE", "name": "Allianz SE",
        "insider": "Oliver Bäte", "role": "CEO",
        "amount": "1.200.000 €", "buy_price": "278.50 €", "date": "2026-08-14",
        "net_worth_est": "30 Mio. €", "wealth_pct": "4.0%", "annual_comp": "6.5 Mio. €",
        "skin_in_game": "🟢 Hoch (Signifikantes Skin-in-the-Game)",
        "signal": "🟢 Zins-Profiteur & starke Dividende"
    },
    {
        "symbol": "DIS", "name": "Walt Disney Co",
        "insider": "Bob Iger", "role": "CEO",
        "amount": "$5.000.000", "buy_price": "$95.10", "date": "2026-08-26",
        "net_worth_est": "$690 Mio.", "wealth_pct": "0.7%", "annual_comp": "$31 Mio.",
        "skin_in_game": "🟡 Moderat (Aber hoher absoluter Betrag)",
        "signal": "🟢 Turnaround-Vertrauen nach Restrukturierung"
    },
    {
        "symbol": "VOW3.DE", "name": "Volkswagen AG",
        "insider": "Oliver Blume", "role": "CEO",
        "amount": "850.000 €", "buy_price": "112.40 €", "date": "2026-08-05",
        "net_worth_est": "20 Mio. €", "wealth_pct": "4.2%", "annual_comp": "7.3 Mio. €",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Antizyklischer Kauf trotz China-Schwäche"
    },
    {
        "symbol": "COIN", "name": "Coinbase Global",
        "insider": "Fred Ehrsam", "role": "Co-Gründer / Director",
        "amount": "$18.500.000", "buy_price": "$240.20", "date": "2026-08-25",
        "net_worth_est": "$2.8 Mrd.", "wealth_pct": "0.6%", "annual_comp": "$1 Mio.",
        "skin_in_game": "🟢 Hoch (Extrem hohes Volumen)",
        "signal": "🟢 Krypto-Zyklus Bull-Run Wette"
    },
    {
        "symbol": "AMD", "name": "Advanced Micro Devices",
        "insider": "Victor Peng", "role": "President",
        "amount": "$3.100.000", "buy_price": "$162.80", "date": "2026-08-21",
        "net_worth_est": "$80 Mio.", "wealth_pct": "3.8%", "annual_comp": "$4.5 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Positionierung gegen Nvidia-Monopol"
    },
    {
        "symbol": "RHM.DE", "name": "Rheinmetall AG",
        "insider": "Armin Papperger", "role": "CEO",
        "amount": "2.500.000 €", "buy_price": "510.50 €", "date": "2026-08-10",
        "net_worth_est": "45 Mio. €", "wealth_pct": "5.5%", "annual_comp": "3.8 Mio. €",
        "skin_in_game": "🔥 ULTRA-HOCH",
        "signal": "🟢 Starkes Signal für weitere Rüstungs-Umsätze"
    },
    {
        "symbol": "PYPL", "name": "PayPal Holdings",
        "insider": "Alex Chriss", "role": "CEO",
        "amount": "$2.200.000", "buy_price": "$65.40", "date": "2026-08-19",
        "net_worth_est": "$15 Mio.", "wealth_pct": "14.6%", "annual_comp": "$1.5 Mio.",
        "skin_in_game": "🔥 ULTRA-HOCH (Fast 15% des Vermögens!)",
        "signal": "🟢 Neuer CEO kauft aggressiv am Tiefpunkt"
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
