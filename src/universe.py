"""Constituents for Market Scanning across US, Germany, and Europe with a focus on Mid/Small Caps and High-Growth."""

# 🇩🇪 Deutschland: SDAX (Deutsche Nebenwerte / Small Caps)
UNIVERSE_DE_SDAX = [
    "SDF.DE", "AM3D.DE", "GFT.DE", "S92.DE", "BC8.DE", "WAF.DE", "DUE.DE",
    "HYQ.DE", "PFV.DE", "STR.DE", "COK.DE", "DWS.DE", "SIX2.DE", "GLJ.DE",
    "ADV.DE", "KCO.DE", "EVT.DE", "MORPH.DE", "NOEJ.DE", "BOS.DE", "AT1.DE"
]

# 🇩🇪 Deutschland: MDAX (Deutsche Mid Caps)
UNIVERSE_DE_MDAX = [
    "PUM.DE", "HFG.DE", "EVK.DE", "LHA.DE", "TKA.DE", "AIXA.DE", "NEM.DE",
    "GXI.DE", "RAA.DE", "FPE.DE", "SZG.DE", "HLE.DE", "KBX.DE", "LEG.DE",
    "TEG.DE", "HOT.DE", "SHA.DE", "TAG.DE", "GYC.DE", "KRN.DE"
]

# 🇩🇪 Deutschland: DAX 40
UNIVERSE_DE_DAX = [
    "SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "MBG.DE", "BMW.DE", "BAS.DE", 
    "DBK.DE", "ADS.DE", "AIR.DE", "RWE.DE", "IFX.DE", "MRK.DE", "VOW3.DE", 
    "MUV2.DE", "HEN3.DE", "BEI.DE", "DTG.DE", "HNR1.DE", "SY1.DE", "HEI.DE",
    "SHL.DE", "EOAN.DE", "FRE.DE", "DB1.DE", "CBK.DE", "ZAL.DE", "ENR.DE"
]

# 🇺🇸 USA: High Growth, Mid Caps, Biotech & Disruptive Stocks (High Momentum / Catalyst Candidates)
UNIVERSE_US_GROWTH_MIDCAPS = [
    "MRNA", "BNTX", "CRSP", "BEAM", "NVCR", "EXAS", "PACB", "IONS", "ALNY", "ROIV",  # Biotech / Pharma
    "PLTR", "CRWD", "SNOW", "ARM", "COIN", "MSTR", "HOOD", "RKLB", "IONQ", "SMCI",   # High-Beta Tech / Disruptive
    "APP", "CELH", "DUOL", "HIMS", "CAVA", "ELF", "ONON", "DKNG", "SOFI", "AFRM",    # High Momentum Mid-Caps
    "SYM", "PATH", "TEM", "ASTS", "JOBY", "ACHR", "QS", "RIVN", "LCID", "RDDT"        # Speculative / Growth
]

# 🇺🇸 USA: S&P / Large Cap Leaders (Reference)
UNIVERSE_US_LEADERS = [
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "AMD",
    "NFLX", "CRM", "ADBE", "QCOM", "MU", "INTC", "IBM", "UBER", "LLY", "UNH", "JPM", "V"
]

# 🇪🇺 Europa: Mid & Growth Champions
UNIVERSE_EU_MID_GROWTH = [
    "ASML.AS", "BESI.AS", "ASM.AS", "SOIT.PA", "VIV.PA", "DSY.PA", "CAP.PA",
    "VATN.SW", "TEMN.SW", "LOGN.SW", "AMS.SW", "NXT.L", "DARK.L", "AUTO.L"
]

CATEGORIZED_UNIVERSES = {
    "🔥 US Mid-Caps & Biotech / High-Beta": UNIVERSE_US_GROWTH_MIDCAPS,
    "🇩🇪 Deutsche Nebenwerte (SDAX)": UNIVERSE_DE_SDAX,
    "🇩🇪 Deutsche Mid-Caps (MDAX)": UNIVERSE_DE_MDAX,
    "🇩🇪 DAX 40": UNIVERSE_DE_DAX,
    "🇪🇺 Europa Mid & Growth": UNIVERSE_EU_MID_GROWTH,
    "🇺🇸 US Large Cap Leaders": UNIVERSE_US_LEADERS
}

FULL_MARKET_UNIVERSE = list(dict.fromkeys(
    UNIVERSE_US_GROWTH_MIDCAPS + UNIVERSE_DE_SDAX + UNIVERSE_DE_MDAX + UNIVERSE_EU_MID_GROWTH + UNIVERSE_DE_DAX + UNIVERSE_US_LEADERS
))
