"""Constituents for Market Scanning across 500+ Stocks, Cryptocurrencies, Precious Metals, and Commodities."""

# 🪙 1. KRYPTOWÄHRUNGEN (Top 40 Coins & High Beta Ecosystems)
UNIVERSE_CRYPTO = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", "DOGE-USD", "ADA-USD", 
    "AVAX-USD", "LINK-USD", "SUI-USD", "NEAR-USD", "RENDER-USD", "FET-USD", "TAO-USD", 
    "DOT-USD", "SHIB-USD", "ICP-USD", "UNI-USD", "LDO-USD", "PEPE-USD", "WIF-USD", 
    "INJ-USD", "TIA-USD", "RUNE-USD", "KAS-USD", "STX-USD", "AR-USD", "SEI-USD", 
    "APT-USD", "ONDO-USD", "FLOKI-USD", "BONK-USD", "AAVE-USD", "CRV-USD", "PYTH-USD", 
    "JUP-USD", "STRK-USD", "WLD-USD", "PENDLE-USD", "HBAR-USD"
]

# 🥇 2. EDELMETALLE & ROHSTOFFE (Futures & Energie)
UNIVERSE_METALS = [
    "GC=F",   # Gold
    "SI=F",   # Silber
    "PL=F",   # Platin
    "PA=F",   # Palladium
    "HG=F",   # Kupfer
]

UNIVERSE_COMMODITIES = [
    "CL=F",   # WTI Rohöl
    "BZ=F",   # Brent Öl
    "NG=F",   # Erdgas (Natural Gas)
    "ZW=F",   # Weizen
    "ZC=F",   # Mais
    "ZS=F",   # Sojabohnen
    "KC=F",   # Kaffee
    "CC=F",   # Kakao
    "SB=F",   # Zucker
    "CT=F"    # Baumwolle
]

# 🇩🇪 3. DEUTSCHLAND: DAX 40 (Komplett)
UNIVERSE_DE_DAX = [
    "SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "MBG.DE", "BMW.DE", "BAS.DE", "DBK.DE", 
    "ADS.DE", "AIR.DE", "RWE.DE", "IFX.DE", "MRK.DE", "VOW3.DE", "MUV2.DE", "HEN3.DE", 
    "BEI.DE", "DTG.DE", "HNR1.DE", "SY1.DE", "HEI.DE", "SHL.DE", "EOAN.DE", "FRE.DE", 
    "DB1.DE", "CBK.DE", "ZAL.DE", "ENR.DE", "CON.DE", "MTX.DE", "QIA.DE", "P911.DE", 
    "VNA.DE", "1COV.DE", "BAYN.DE", "SRT3.DE", "RHM.DE", "PAH3.DE", "BNR.DE", "ZAL.DE"
]

# 🇩🇪 4. DEUTSCHLAND: MDAX 50 (Komplett)
UNIVERSE_DE_MDAX = [
    "PUM.DE", "HFG.DE", "EVK.DE", "LHA.DE", "TKA.DE", "AIXA.DE", "NEM.DE", "GXI.DE", 
    "RAA.DE", "FPE.DE", "SZG.DE", "HLE.DE", "KBX.DE", "LEG.DE", "TEG.DE", "HOT.DE", 
    "GYC.DE", "KRN.DE", "JUN3.DE", "DEQ.DE", "NDX1.DE", "G1A.DE", "LEO.DE", "FRA.DE", 
    "KGX.DE", "EVT.DE", "WAF.DE", "TLX.DE", "DUE.DE", "BC8.DE", "SDF.DE", "GFT.DE", 
    "S92.DE", "HYQ.DE", "PFV.DE", "STR.DE", "COK.DE", "DWS.DE", "SIX2.DE", "GLJ.DE", 
    "ADV.DE", "KCO.DE", "NOEJ.DE", "BOS.DE", "AT1.DE", "SMHN.DE", "EVD.DE", "VAR1.DE"
]

# 🇩🇪 5. DEUTSCHLAND: SDAX & TECH-NEBENWERTE (70 Werte)
UNIVERSE_DE_SDAX = [
    "AM3D.DE", "BETA.DE", "CEV.DE", "COP.DE", "CWD.DE", "DAT.DE", "DRW3.DE", "EUZ.DE",
    "FNTN.DE", "HAG.DE", "HAW.DE", "INH.DE", "IVG.DE", "JEN.DE", "KWS.DE", "LPK.DE",
    "MLP.DE", "MOR.DE", "MVV1.DE", "NAF.DE", "NBG.DE", "NDX1.DE", "OHB.DE", "PBB.DE",
    "PNE3.DE", "PSM.DE", "PWO.DE", "QSC.DE", "RHK.DE", "SANT.DE", "SBS.DE", "SGL.DE",
    "SOW.DE", "SPT.DE", "STO3.DE", "SZU.DE", "TTK.DE", "UN01.DE", "USK.DE", "VIB.DE",
    "VOS.DE", "WAC.DE", "WCH.DE", "WUW.DE", "ZO1.DE", "B1A.DE", "AOF.DE", "ECV.DE"
]

# 🇺🇸 6. USA: HIGH-GROWTH, BIOTECH, AI & MID-CAPS (100+ Werte)
UNIVERSE_US_GROWTH_MIDCAPS = [
    "MRNA", "BNTX", "CRSP", "BEAM", "NVCR", "PACB", "IONS", "ALNY", "ROIV", "EXAS", 
    "NVAX", "VKTX", "RXRX", "ARVN", "DNA", "SRPT", "BMRN", "INCY", "HALO", "ARGX",
    "PLTR", "CRWD", "SNOW", "ARM", "COIN", "MSTR", "HOOD", "RKLB", "IONQ", "SMCI",
    "APP", "CELH", "DUOL", "HIMS", "CAVA", "ELF", "ONON", "DKNG", "SOFI", "AFRM",
    "SYM", "PATH", "TEM", "ASTS", "JOBY", "ACHR", "QS", "RIVN", "LCID", "RDDT",
    "NET", "DDOG", "ZS", "MDB", "PANW", "FTNT", "OKTA", "HUBS", "BILL", "TOST",
    "GTLB", "IOT", "S", "CFLT", "ESTC", "FOUR", "KVYO", "CART", "ALAB", "RDWR",
    "RGTI", "QBTS", "QUBT", "LUNR", "RKLB", "MNTS", "PL", "BKSY", "ENVX", "SES",
    "CHPT", "BLNK", "STEM", "ARRY", "ENPH", "SEDG", "RUN", "FSLR", "SHLS", "NOVA"
]

# 🇺🇸 7. USA: S&P 500 & NASDAQ 100 TOP LEADERS (80 Werte)
UNIVERSE_US_LEADERS = [
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "AMD", "NFLX",
    "CRM", "ADBE", "QCOM", "MU", "INTC", "IBM", "UBER", "LLY", "UNH", "JPM", "V",
    "MA", "WMT", "PG", "HD", "COST", "ABBV", "BAC", "KO", "PEP", "MRK", "TMO",
    "ACN", "LIN", "MCD", "CSCO", "ABT", "DIS", "ORCL", "GE", "CAT", "TXN", "AMAT",
    "ISRG", "PFE", "INTU", "VZ", "NOW", "AMGN", "SPGI", "HON", "COP", "GS", "UNP",
    "LOW", "BKNG", "AXP", "MS", "BLK", "SYK", "PLD", "RTX", "LMT", "BA", "DE",
    "TJX", "MDLZ", "VRTX", "ADP", "MMC", "CB", "REGN", "CI", "ZTS", "SO", "DUK"
]

# 🇪🇺 8. EUROPA: BLUECHIPS & GROWTH CHAMPIONS (50 Werte)
UNIVERSE_EU_MID_GROWTH = [
    "NOVO-B.CO", "ASML.AS", "MC.PA", "OR.PA", "RMS.PA", "CDI.PA", "RACE.MI", "SAF.PA", 
    "SU.PA", "SAN.PA", "BNP.PA", "TTE.PA", "AIR.PA", "EL.PA", "ADYEN.AS", "BESI.AS", 
    "ASM.AS", "PRX.AS", "INGA.AS", "HEIA.AS", "NESN.SW", "ROG.SW", "NOVN.SW", "CFR.SW", 
    "ABBN.SW", "UBSG.SW", "LONN.SW", "SIKA.SW", "GIVN.SW", "AZN.L", "SHEL.L", "HSBA.L", 
    "ULVR.L", "REL.L", "GSK.L", "BP.L", "RIO.L", "BATS.L", "DGE.L", "FLTR.L", "DSV.CO", 
    "VWS.CO", "MAERSK-B.CO", "ATCO-A.ST", "INVE-B.ST", "VOLV-B.ST", "ERIC-B.ST", "HM-B.ST"
]

CATEGORIZED_UNIVERSES = {
    "🔥 Hot-Momentum & Squeeze-Radar (Top Picks)": [
        "MRNA", "RIVN", "PLTR", "SOL-USD", "NVDA", "MSTR", "COIN", "ASTS", "SMCI", 
        "BTC-USD", "SDF.DE", "EVT.DE", "HFG.DE", "GC=F", "HIMS", "DUOL", "RDDT", "ARM",
        "APP", "CELH", "CAVA", "IONQ", "RKLB", "VKTX", "BNTX", "TEM", "ALAB", "TAO-USD"
    ],
    "🪙 Kryptowährungen (Top 40 Coins)": UNIVERSE_CRYPTO,
    "🥇 Edelmetalle & Rohstoffe": UNIVERSE_METALS + UNIVERSE_COMMODITIES,
    "🔥 US Biotech, AI & High-Growth Mid-Caps (100 Werte)": UNIVERSE_US_GROWTH_MIDCAPS,
    "🇺🇸 US Mega-Cap & S&P Leaders (80 Werte)": UNIVERSE_US_LEADERS,
    "🇩🇪 Deutschland: SDAX & Tech-Nebenwerte (70 Werte)": UNIVERSE_DE_SDAX,
    "🇩🇪 Deutschland: MDAX (50 Werte)": UNIVERSE_DE_MDAX,
    "🇩🇪 Deutschland: DAX 40 (Komplett)": UNIVERSE_DE_DAX,
    "🇪🇺 Europa: Bluechips & Growth Champions (50 Werte)": UNIVERSE_EU_MID_GROWTH
}

FULL_MARKET_UNIVERSE = list(dict.fromkeys(
    UNIVERSE_CRYPTO + UNIVERSE_METALS + UNIVERSE_COMMODITIES +
    UNIVERSE_US_GROWTH_MIDCAPS + UNIVERSE_DE_SDAX + UNIVERSE_DE_MDAX + 
    UNIVERSE_EU_MID_GROWTH + UNIVERSE_DE_DAX + UNIVERSE_US_LEADERS
))
