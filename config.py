"""Configuration for the Multi-Asset Finance Decision Support System."""

# Predefined watchlists for quick selection across all asset classes
WATCHLISTS = {
    "🪙 Kryptowährungen": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", "DOGE-USD", "AVAX-USD", "LINK-USD"],
    "🥇 Edelmetalle": ["GC=F", "SI=F", "PL=F", "PA=F", "HG=F"],
    "🛢️ Rohstoffe & Energie": ["CL=F", "BZ=F", "NG=F", "ZW=F", "KC=F", "CC=F"],
    "🇺🇸 US Tech Leaders": ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"],
    "🇩🇪 DAX / Deutschland": ["SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "MBG.DE", "BMW.DE", "BAS.DE"],
    "🇩🇪 SDAX Deutsche Nebenwerte": ["SDF.DE", "GFT.DE", "WAF.DE", "BC8.DE", "DWS.DE", "EVT.DE"],
    "🇪🇺 Europa Champions": ["ASML.AS", "BESI.AS", "AIR.PA", "CAP.PA", "DSY.PA"],
    "⚡ High Growth / Disruptiv": ["MRNA", "PLTR", "CRWD", "SNOW", "ARM", "COIN", "MSTR", "RKLB"]
}

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
