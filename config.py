"""Configuration for the Finance Decision Support System."""

# Predefined watchlists for quick selection
WATCHLISTS = {
    "???? US Tech Leaders": ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"],
    "???? DAX / Deutschland": ["SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "MBG.DE", "BMW.DE", "BAS.DE"],
    "???? Europa Champions": ["ASML.AS", "MC.PA", "OR.PA", "AIR.PA", "NESN.SW", "NOVN.SW", "AZN.L"],
    "?? US Dividenden & Value": ["JNJ", "PG", "KO", "PEP", "ABBV", "XOM", "CVX"],
    "? High Growth / Disruptiv": ["PLTR", "CRWD", "SNOW", "ARM", "AMD", "COIN"]
}

# Scoring Thresholds & Parameters
TECHNICAL_CONFIG = {
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "ema_fast": 20,
    "ema_medium": 50,
    "sma_slow": 200,
    "bb_period": 20,
    "bb_std": 2.0
}

FUNDAMENTAL_THRESHOLDS = {
    "pe_low": 15.0,
    "pe_fair": 25.0,
    "pe_high": 40.0,
    "peg_good": 1.5,
    "roe_good": 0.15,       # 15%
    "debt_to_equity_max": 1.5,
    "fcf_yield_good": 0.04   # 4%
}
