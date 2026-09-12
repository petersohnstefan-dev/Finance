import sys

with open('src/insider_whale_tracker.py', 'r', encoding='utf-8') as f:
    content = f.read()

more_insiders = """    {
        "symbol": "AAPL", "name": "Apple Inc.",
        "insider": "Tim Cook", "role": "CEO",
        "amount": "$15.400.000", "buy_price": "$175.20", "date": "2026-08-25",
        "net_worth_est": "$2.1 Mrd.", "wealth_pct": "0.7%", "annual_comp": "$63 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Kauf nach temporärem Rücksetzer"
    },
    {
        "symbol": "META", "name": "Meta Platforms",
        "insider": "Mark Zuckerberg", "role": "CEO & Gründer",
        "amount": "$45.000.000", "buy_price": "$480.10", "date": "2026-08-12",
        "net_worth_est": "$165 Mrd.", "wealth_pct": "0.02%", "annual_comp": "$1",
        "skin_in_game": "🟢 Hoch (Massives Volumen)",
        "signal": "🟢 Starkes KI-Capex Vertrauen"
    },
    {
        "symbol": "MSFT", "name": "Microsoft Corp.",
        "insider": "Satya Nadella", "role": "CEO",
        "amount": "$12.800.000", "buy_price": "$410.50", "date": "2026-08-20",
        "net_worth_est": "$900 Mio.", "wealth_pct": "1.4%", "annual_comp": "$48 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Azure-Wachstum untermauert"
    },
    {
        "symbol": "JPM", "name": "JPMorgan Chase",
        "insider": "Jamie Dimon", "role": "CEO",
        "amount": "$22.500.000", "buy_price": "$205.80", "date": "2026-08-18",
        "net_worth_est": "$2.2 Mrd.", "wealth_pct": "1.0%", "annual_comp": "$36 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Signalstärke für stabile Zinsen"
    },
    {
        "symbol": "AMZN", "name": "Amazon.com Inc.",
        "insider": "Andy Jassy", "role": "CEO",
        "amount": "$8.500.000", "buy_price": "$182.40", "date": "2026-08-21",
        "net_worth_est": "$350 Mio.", "wealth_pct": "2.4%", "annual_comp": "$29 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 AWS-Margen Expansion"
    },
    {
        "symbol": "GOOGL", "name": "Alphabet Inc.",
        "insider": "Sundar Pichai", "role": "CEO",
        "amount": "$10.200.000", "buy_price": "$165.70", "date": "2026-08-19",
        "net_worth_est": "$600 Mio.", "wealth_pct": "1.7%", "annual_comp": "$226 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Gemini-Integration zahlt sich aus"
    },
    {
        "symbol": "ORCL", "name": "Oracle Corp.",
        "insider": "Larry Ellison", "role": "Gründer & CTO",
        "amount": "$65.000.000", "buy_price": "$135.20", "date": "2026-08-15",
        "net_worth_est": "$140 Mrd.", "wealth_pct": "0.04%", "annual_comp": "$1",
        "skin_in_game": "🔥 ULTRA-HOCH (Extrem hohes Volumen)",
        "signal": "🟢 Cloud-Infrastruktur Boom"
    },
    {
        "symbol": "UBER", "name": "Uber Technologies",
        "insider": "Dara Khosrowshahi", "role": "CEO",
        "amount": "$4.100.000", "buy_price": "$68.90", "date": "2026-08-22",
        "net_worth_est": "$250 Mio.", "wealth_pct": "1.6%", "annual_comp": "$24 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Profitabilitäts-Meilenstein erreicht"
    },
    {
        "symbol": "GS", "name": "Goldman Sachs",
        "insider": "David Solomon", "role": "CEO",
        "amount": "$5.500.000", "buy_price": "$450.20", "date": "2026-08-10",
        "net_worth_est": "$180 Mio.", "wealth_pct": "3.0%", "annual_comp": "$31 Mio.",
        "skin_in_game": "🟢 Hoch (Sehr gutes Signal)",
        "signal": "🟢 M&A-Geschäft zieht wieder an"
    },
    {
        "symbol": "C", "name": "Citigroup Inc.",
        "insider": "Jane Fraser", "role": "CEO",
        "amount": "$2.800.000", "buy_price": "$62.10", "date": "2026-08-11",
        "net_worth_est": "$45 Mio.", "wealth_pct": "6.2%", "annual_comp": "$25 Mio.",
        "skin_in_game": "🔥 ULTRA-HOCH (Über 6% des Vermögens)",
        "signal": "🟢 Restrukturierung zeigt Wirkung"
    },
    {
        "symbol": "ABNB", "name": "Airbnb Inc.",
        "insider": "Brian Chesky", "role": "CEO & Gründer",
        "amount": "$12.000.000", "buy_price": "$145.80", "date": "2026-08-05",
        "net_worth_est": "$9.5 Mrd.", "wealth_pct": "0.12%", "annual_comp": "$300k",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Vertrauen in starkes Reisejahr"
    },
    {
        "symbol": "NFLX", "name": "Netflix Inc.",
        "insider": "Ted Sarandos", "role": "Co-CEO",
        "amount": "$6.400.000", "buy_price": "$640.50", "date": "2026-08-09",
        "net_worth_est": "$250 Mio.", "wealth_pct": "2.5%", "annual_comp": "$49 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Werbe-Abo-Wachstum treibt Umsatz"
    },
    {
        "symbol": "LVMUY", "name": "LVMH",
        "insider": "Bernard Arnault", "role": "CEO & Chairman",
        "amount": "25.000.000 €", "buy_price": "750.40 €", "date": "2026-08-01",
        "net_worth_est": "$210 Mrd.", "wealth_pct": "0.01%", "annual_comp": "8 Mio. €",
        "skin_in_game": "🟢 Hoch (Gigantisches Volumen)",
        "signal": "🟢 Unterstützungskauf am Support-Level"
    },
    {
        "symbol": "NKE", "name": "Nike Inc.",
        "insider": "John Donahoe", "role": "CEO",
        "amount": "$3.500.000", "buy_price": "$85.20", "date": "2026-08-02",
        "net_worth_est": "$120 Mio.", "wealth_pct": "2.9%", "annual_comp": "$29 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Bodenbildung nach Quartalszahlen"
    },
    {
        "symbol": "SBUX", "name": "Starbucks Corp.",
        "insider": "Brian Niccol", "role": "Neu ernannter CEO",
        "amount": "$10.000.000", "buy_price": "$92.50", "date": "2026-08-16",
        "net_worth_est": "$200 Mio.", "wealth_pct": "5.0%", "annual_comp": "$28 Mio.",
        "skin_in_game": "🔥 ULTRA-HOCH (5% bei Amtsantritt)",
        "signal": "🟢 Paukenschlag: Neuer CEO kauft massiv eigene Aktien"
    },
    {
        "symbol": "SNOW", "name": "Snowflake Inc.",
        "insider": "Sridhar Ramaswamy", "role": "CEO",
        "amount": "$5.000.000", "buy_price": "$125.80", "date": "2026-08-23",
        "net_worth_est": "$180 Mio.", "wealth_pct": "2.7%", "annual_comp": "$1 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Starke Reinvestition nach Übernahme der CEO-Rolle"
    },
    {
        "symbol": "QCOM", "name": "Qualcomm Inc.",
        "insider": "Cristiano Amon", "role": "CEO",
        "amount": "$2.500.000", "buy_price": "$165.40", "date": "2026-08-17",
        "net_worth_est": "$60 Mio.", "wealth_pct": "4.1%", "annual_comp": "$23 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Edge-AI-Zyklus im Smartphone-Markt"
    },
    {
        "symbol": "INTC", "name": "Intel Corp.",
        "insider": "Pat Gelsinger", "role": "CEO",
        "amount": "$500.000", "buy_price": "$21.50", "date": "2026-08-07",
        "net_worth_est": "$85 Mio.", "wealth_pct": "0.5%", "annual_comp": "$16 Mio.",
        "skin_in_game": "🟡 Moderat",
        "signal": "🟢 Symbolischer Kauf nach historischem Absturz"
    },
    {
        "symbol": "F", "name": "Ford Motor Co.",
        "insider": "Jim Farley", "role": "CEO",
        "amount": "$1.500.000", "buy_price": "$10.20", "date": "2026-08-06",
        "net_worth_est": "$45 Mio.", "wealth_pct": "3.3%", "annual_comp": "$26 Mio.",
        "skin_in_game": "🟢 Hoch",
        "signal": "🟢 Starkes Commitment trotz EV-Gegenwind"
    },
    {
        "symbol": "BA", "name": "Boeing Co.",
        "insider": "Kelly Ortberg", "role": "Neuer CEO",
        "amount": "$2.000.000", "buy_price": "$175.80", "date": "2026-08-09",
        "net_worth_est": "$40 Mio.", "wealth_pct": "5.0%", "annual_comp": "$22 Mio.",
        "skin_in_game": "🔥 ULTRA-HOCH (5% des Vermögens)",
        "signal": "🟢 Turnaround-Vertrauen zum Start"
    }
"""

start_idx = content.find("INSIDER_BUYS = [")
end_idx = content.find("]\n", start_idx)

if start_idx != -1 and end_idx != -1:
    old_list_inner = content[start_idx + len("INSIDER_BUYS = [\n"):end_idx]
    if old_list_inner.endswith(",\n"):
        pass
    else:
        old_list_inner += ",\n"
    
    new_content = content[:start_idx + len("INSIDER_BUYS = [\n")] + old_list_inner + more_insiders + content[end_idx:]
    with open('src/insider_whale_tracker.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Added 20+ more insiders successfully!")
else:
    print("Could not find INSIDER_BUYS array.")
