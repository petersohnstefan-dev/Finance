import sys
import re

with open('src/insider_whale_tracker.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace the INSIDER_BUYS list.
# Let's define the massive list:

new_insider_buys = """INSIDER_BUYS = [
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
]"""

# Replace the block from INSIDER_BUYS = [ to the closing ]
# Find the start and end indices of the INSIDER_BUYS list
start_idx = content.find("INSIDER_BUYS = [")
if start_idx != -1:
    end_idx = content.find("]\n", start_idx) + 1
    if end_idx != 0:
        new_content = content[:start_idx] + new_insider_buys + content[end_idx:]
        with open('src/insider_whale_tracker.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully updated INSIDER_BUYS.")
    else:
        print("End index not found.")
else:
    print("Start index not found.")

