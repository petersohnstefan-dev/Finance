"""Constituents for Market Scanning across Stocks, Cryptocurrencies, Precious Metals, and Commodities."""

# 🪙 KRYPTOWÄHRUNGEN (Top Coins & High Beta)
UNIVERSE_CRYPTO = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", 
    "DOGE-USD", "ADA-USD", "AVAX-USD", "LINK-USD", "SUI-USD", 
    "NEAR-USD", "RENDER-USD", "FET-USD", "TAO-USD"
]

# 🥇 EDELMETALLE (Futures & Rohstoff-Werte)
UNIVERSE_METALS = [
    "GC=F",   # Gold Futures
    "SI=F",   # Silber Futures
    "PL=F",   # Platin Futures
    "PA=F",   # Palladium Futures
    "HG=F"    # Kupfer Futures
]

# 🛢️ ENERGIE & ROHSTOFFE (Commodities & Agrar)
UNIVERSE_COMMODITIES = [
    "CL=F",   # WTI Rohöl Futures
    "BZ=F",   # Brent Crude Oil Futures
    "NG=F",   # Erdgas (Natural Gas) Futures
    "ZW=F",   # Weizen (Wheat) Futures
    "ZC=F",   # Mais (Corn) Futures
    "KC=F",   # Kaffee (Coffee) Futures
    "CC=F"    # Kakao (Cocoa) Futures
]

# 🇩🇪 Deutschland: SDAX (Deutsche Nebenwerte / Small Caps)
UNIVERSE_DE_SDAX = [
    "SDF.DE", "GFT.DE", "S92.DE", "BC8.DE", "WAF.DE", "DUE.DE",
    "HYQ.DE", "PFV.DE", "STR.DE", "COK.DE", "DWS.DE", "SIX2.DE", "GLJ.DE",
    "ADV.DE", "KCO.DE", "EVT.DE", "NOEJ.DE", "BOS.DE", "AT1.DE"
]

# 🇩🇪 Deutschland: MDAX (Deutsche Mid Caps)
UNIVERSE_DE_MDAX = [
    "PUM.DE", "HFG.DE", "EVK.DE", "LHA.DE", "TKA.DE", "AIXA.DE", "NEM.DE",
    "GXI.DE", "RAA.DE", "FPE.DE", "SZG.DE", "HLE.DE", "KBX.DE", "LEG.DE",
    "TEG.DE", "HOT.DE", "GYC.DE", "KRN.DE"
]

# 🇩🇪 Deutschland: DAX 40
UNIVERSE_DE_DAX = [
    "SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "MBG.DE", "BMW.DE", "BAS.DE", 
    "DBK.DE", "ADS.DE", "AIR.DE", "RWE.DE", "IFX.DE", "MRK.DE", "VOW3.DE", 
    "MUV2.DE", "HEN3.DE", "BEI.DE", "DTG.DE", "HNR1.DE", "SY1.DE", "HEI.DE",
    "SHL.DE", "EOAN.DE", "FRE.DE", "DB1.DE", "CBK.DE", "ZAL.DE", "ENR.DE"
]

# 🇺🇸 USA: High Growth, Mid Caps, Biotech & Disruptive Stocks
UNIVERSE_US_GROWTH_MIDCAPS = [
    "MRNA", "BNTX", "CRSP", "BEAM", "NVCR", "PACB", "IONS", "ALNY", "ROIV",
    "PLTR", "CRWD", "SNOW", "ARM", "COIN", "MSTR", "HOOD", "RKLB", "IONQ", "SMCI",
    "APP", "CELH", "DUOL", "HIMS", "CAVA", "ELF", "ONON", "DKNG", "SOFI", "AFRM",
    "SYM", "PATH", "TEM", "ASTS", "JOBY", "ACHR", "QS", "RIVN", "LCID", "RDDT"
]

# 🇺🇸 USA: S&P / Large Cap Leaders
UNIVERSE_US_LEADERS = [
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "AMD",
    "NFLX", "CRM", "ADBE", "QCOM", "MU", "INTC", "IBM", "UBER", "LLY", "UNH", "JPM", "V"
]

# 🇪🇺 Europa: Mid & Growth Champions
UNIVERSE_EU_MID_GROWTH = [
    "ASML.AS", "BESI.AS", "ASM.AS", "VIV.PA", "DSY.PA", "CAP.PA",
    "VATN.SW", "TEMN.SW", "LOGN.SW", "AMS.SW", "NXT.L", "AUTO.L"
]

CATEGORIZED_UNIVERSES = {
    "🪙 Kryptowährungen": UNIVERSE_CRYPTO,
    "🥇 Edelmetalle": UNIVERSE_METALS,
    "🛢️ Rohstoffe & Energie": UNIVERSE_COMMODITIES,
    "🔥 US Mid-Caps & Biotech": UNIVERSE_US_GROWTH_MIDCAPS,
    "🇩🇪 Deutsche Nebenwerte (SDAX)": UNIVERSE_DE_SDAX,
    "🇩🇪 Deutsche Mid-Caps (MDAX)": UNIVERSE_DE_MDAX,
    "🇩🇪 DAX 40": UNIVERSE_DE_DAX,
    "🇪🇺 Europa Mid & Growth": UNIVERSE_EU_MID_GROWTH,
    "🇺🇸 US Large Cap Leaders": UNIVERSE_US_LEADERS
}

FULL_MARKET_UNIVERSE = list(dict.fromkeys(
    UNIVERSE_CRYPTO + UNIVERSE_METALS + UNIVERSE_COMMODITIES +
    UNIVERSE_US_GROWTH_MIDCAPS + UNIVERSE_DE_SDAX + UNIVERSE_DE_MDAX + 
    UNIVERSE_EU_MID_GROWTH + UNIVERSE_DE_DAX + UNIVERSE_US_LEADERS
))
