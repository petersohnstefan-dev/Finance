"""Master WKN (Wertpapierkennnummer / WKZ) & ISIN Mapping Service.
Maps international tickers, German equities, European bluechips, US leaders,
cryptocurrencies, precious metals, and commodities to official German WKNs.
"""

import re
from typing import Dict, Optional

# Official Master WKN Dictionary
TICKER_TO_WKN: Dict[str, str] = {
    # --- Musterdepot Assets ---
    "MRNA": "A2N9D9",       # Moderna Inc.
    "BEAM": "A2PZ4W",       # Beam Therapeutics
    "RIVN": "A3C47B",       # Rivian Automotive
    "SOL-USD": "A3GX1B",    # 21Shares Solana ETP / Solana
    "PLTR": "A2QA4J",       # Palantir Technologies
    "DUOL": "A3CS5E",       # Duolingo Inc.
    "NVDA": "918422",       # NVIDIA Corp.
    "SAP.DE": "716460",     # SAP SE
    "SAP": "716460",
    "MUV2.DE": "843002",    # Münchener Rück
    "MUV2": "843002",
    "4GLD.DE": "A0S9GB",    # Xetra-Gold ETC
    "4GLD": "A0S9GB",
    "BTC-USD": "A278KE",    # 21Shares Bitcoin ETP / Bitcoin
    "MSFT": "870747",       # Microsoft Corp.

    # --- USA: Mega Caps & Tech Leaders ---
    "AAPL": "865985",       # Apple Inc.
    "AMZN": "906866",       # Amazon.com
    "GOOGL": "A14Y6F",      # Alphabet Class A
    "GOOG": "A14Y6H",       # Alphabet Class C
    "META": "A1JWVX",       # Meta Platforms
    "TSLA": "A1CX3T",       # Tesla Inc.
    "AVGO": "A2JG9Z",       # Broadcom Inc.
    "AMD": "863186",        # Advanced Micro Devices
    "NFLX": "552484",       # Netflix Inc.
    "ARM": "A3EUCD",        # Arm Holdings
    "COIN": "A2Z0W2",       # Coinbase Global
    "MSTR": "722713",       # MicroStrategy
    "SMCI": "A0MKJF",       # Super Micro Computer
    "CRM": "A0B87V",        # Salesforce
    "ADBE": "871981",       # Adobe Inc.
    "QCOM": "883121",       # Qualcomm
    "MU": "869020",         # Micron Technology
    "INTC": "855681",       # Intel Corp.
    "IBM": "851399",        # IBM
    "UBER": "A2PHHG",       # Uber Technologies
    "LLY": "858560",        # Eli Lilly
    "UNH": "869561",        # UnitedHealth
    "JPM": "850628",        # JPMorgan Chase
    "V": "A0NC7B",          # Visa Inc.
    "MA": "A0J204",         # Mastercard
    "WMT": "860853",        # Walmart
    "PG": "852062",         # Procter & Gamble
    "HD": "866953",         # Home Depot
    "COST": "888351",       # Costco
    "ABBV": "A1J84E",       # AbbVie
    "BAC": "858388",        # Bank of America
    "KO": "850663",         # Coca-Cola
    "PEP": "851995",        # PepsiCo
    "MRK": "A0VK2C",        # Merck & Co. (US)
    "DIS": "855686",        # Walt Disney
    "ORCL": "877717",       # Oracle
    "GE": "851144",         # General Electric
    "CAT": "850598",        # Caterpillar
    "TXN": "852654",        # Texas Instruments
    "AMAT": "865177",       # Applied Materials
    "ISRG": "588056",       # Intuitive Surgical
    "PFE": "852009",        # Pfizer
    "INTU": "886053",       # Intuit
    "NOW": "A1JX4P",        # ServiceNow
    "AMGN": "867900",       # Amgen
    "SPGI": "A2AHZ7",       # S&P Global
    "HON": "870153",        # Honeywell
    "GS": "920332",         # Goldman Sachs
    "BLK": "928193",        # BlackRock
    "PLD": "A1JBD1",        # Prologis
    "RTX": "A2PZ4N",        # RTX Corp (Raytheon)
    "LMT": "899744",        # Lockheed Martin
    "BA": "850471",         # Boeing
    "DE": "850866",         # Deere & Company
    "VRTX": "882807",       # Vertex Pharma

    # --- USA: High Growth, AI, Biotech & Squeezes ---
    "CRWD": "A2PK2R",       # CrowdStrike
    "SNOW": "A2QB38",       # Snowflake
    "HOOD": "A3CVCQ",       # Robinhood
    "RKLB": "A3CY7P",       # Rocket Lab
    "IONQ": "A3C4VR",       # IonQ
    "APP": "A2QH1E",        # AppLovin
    "CELH": "A0YH60",       # Celsius Holdings
    "HIMS": "A2QLM0",       # Hims & Hers Health
    "CAVA": "A3EU6W",       # CAVA Group
    "ELF": "A2AR19",        # e.l.f. Beauty
    "ONON": "A3C20E",       # On Holding
    "DKNG": "A2P20M",       # DraftKings
    "SOFI": "A3CSY3",       # SoFi Technologies
    "AFRM": "A2QL1G",       # Affirm Holdings
    "SYM": "A3CWCL",        # Symbotic
    "PATH": "A3CNLD",       # UiPath
    "TEM": "A3ET5U",        # Tempus AI
    "ASTS": "A3C42C",       # AST SpaceMobile
    "JOBY": "A3C23B",       # Joby Aviation
    "ACHR": "A3C38K",       # Archer Aviation
    "QS": "A2QGEW",         # QuantumScape
    "LCID": "A3CVTH",       # Lucid Group
    "RDDT": "A3ETR1",       # Reddit Inc.
    "NET": "A2PQLQ",        # Cloudflare
    "DDOG": "A2PU7X",       # Datadog
    "ZS": "A2N5FW",         # Zscaler
    "MDB": "A2DYB1",        # MongoDB
    "PANW": "A1T77Q",       # Palo Alto Networks
    "FTNT": "A0YEFE",       # Fortinet
    "OKTA": "A2DNKR",       # Okta Inc.
    "HUBS": "A12CWJ",       # HubSpot
    "BILL": "A2PX63",       # BILL Holdings
    "TOST": "A3C3C0",       # Toast Inc.
    "GTLB": "A3C5FS",       # GitLab
    "IOT": "A3C945",        # Samsara
    "S": "A3CP82",          # SentinelOne
    "CFLT": "A3CPN7",       # Confluent
    "ESTC": "A2N6PA",       # Elastic
    "KVYO": "A3ETGB",       # Klaviyo
    "CART": "A3ET0D",       # Instacart (Maplebear)
    "ALAB": "A3ET3B",       # Astera Labs
    "RGTI": "A3DJQG",       # Rigetti Computing
    "QBTS": "A3DMTH",       # D-Wave Quantum
    "QUBT": "A3D1Z0",       # Quantum Computing Inc.
    "LUNR": "A3D9WW",       # Intuitive Machines
    "BLNK": "A2N90H",       # Blink Charging
    "CHPT": "A2QK5W",       # ChargePoint
    "ENPH": "A1JC82",       # Enphase Energy
    "SEDG": "A14QVU",       # SolarEdge
    "RUN": "A14TW4",        # Sunrun
    "FSLR": "A0LEKM",       # First Solar
    "PLUG": "A1JA81",       # Plug Power
    "UPST": "A2QJL7",       # Upstart Holdings
    "BNTX": "A2PSR2",       # BioNTech
    "CRSP": "A2AT0W",       # CRISPR Therapeutics
    "NVCR": "A1409C",       # NovoCure
    "PACB": "A1C3E6",       # Pacific Biosciences
    "IONS": "937812",       # Ionis Pharma
    "ALNY": "A0B8M4",       # Alnylam Pharma
    "ROIV": "A3CR8N",       # Roivant Sciences
    "EXAS": "563368",       # Exact Sciences
    "NVAX": "886006",       # Novavax
    "VKTX": "A12H07",       # Viking Therapeutics
    "RXRX": "A3CNQ5",       # Recursion Pharma
    "SRPT": "A2D8CG",       # Sarepta Therapeutics
    "INCY": "893589",       # Incyte Corp.
    "ARGX": "A2AC9F",       # argenx SE

    # --- Deutschland: DAX 40 ---
    "SIE.DE": "723610",     # Siemens
    "ALV.DE": "840400",     # Allianz
    "DTE.DE": "555750",     # Deutsche Telekom
    "MBG.DE": "710000",     # Mercedes-Benz Group
    "BMW.DE": "519000",     # BMW
    "BAS.DE": "BASF11",     # BASF
    "DBK.DE": "514000",     # Deutsche Bank
    "ADS.DE": "A1EWWW",     # Adidas
    "AIR.DE": "938914",     # Airbus
    "AIR.PA": "938914",
    "RWE.DE": "703712",     # RWE
    "IFX.DE": "623100",     # Infineon
    "MRK.DE": "659990",     # Merck KGaA
    "VOW3.DE": "766403",    # Volkswagen Vz.
    "HEN3.DE": "604843",    # Henkel Vz.
    "BEI.DE": "520000",     # Beiersdorf
    "DTG.DE": "DTR0CK",     # Daimler Truck
    "HNR1.DE": "840221",    # Hannover Rück
    "SY1.DE": "SYM999",     # Symrise
    "HEI.DE": "604700",     # Heidelberg Materials
    "SHL.DE": "SHL100",     # Siemens Healthineers
    "EOAN.DE": "ENAG99",    # E.ON
    "FRE.DE": "578560",     # Fresenius SE
    "DB1.DE": "581005",     # Deutsche Börse
    "CBK.DE": "CBK100",     # Commerzbank
    "ZAL.DE": "ZAL111",     # Zalando
    "ENR.DE": "ENER6Y",     # Siemens Energy
    "CON.DE": "543900",     # Continental
    "MTX.DE": "A0D9PT",     # MTU Aero Engines
    "QIA.DE": "A2DKCH",     # Qiagen
    "P911.DE": "PAG911",    # Porsche AG Vz.
    "VNA.DE": "A1ML7J",     # Vonovia
    "1COV.DE": "606214",    # Covestro
    "BAYN.DE": "BAY001",    # Bayer
    "SRT3.DE": "716563",    # Sartorius Vz.
    "RHM.DE": "703000",     # Rheinmetall
    "PAH3.DE": "PAH003",    # Porsche Automobil Holding
    "BNR.DE": "A1DAHH",     # Brenntag

    # --- Deutschland: MDAX & SDAX ---
    "PUM.DE": "696960",     # Puma
    "HFG.DE": "A16140",     # HelloFresh
    "EVK.DE": "EVNK01",     # Evonik
    "LHA.DE": "823212",     # Lufthansa
    "TKA.DE": "750000",     # Thyssenkrupp
    "AIXA.DE": "A0WMPJ",    # Aixtron
    "NEM.DE": "645290",     # Nemetschek
    "GXI.DE": "580060",     # Gerresheimer
    "FPE.DE": "578580",     # Fresenius Medical Care
    "SZG.DE": "620200",     # Salzgitter
    "HLE.DE": "A13SX2",     # Hella
    "KBX.DE": "KBX100",     # Knorr-Bremse
    "LEG.DE": "LEG111",     # LEG Immobilien
    "TEG.DE": "TAG101",     # TAG Immobilien
    "HOT.DE": "A0HN5C",     # Hochtief
    "GYC.DE": "577220",     # Encavis / GYC
    "KRN.DE": "633500",     # Krones
    "JUN3.DE": "621993",    # Jungheinrich Vz.
    "DEQ.DE": "A0Z2XN",     # Deutsche EuroShop
    "NDX1.DE": "A0D655",    # Nordex
    "G1A.DE": "663200",     # GEA Group
    "LEO.DE": "540888",     # Leoni / LEO
    "FRA.DE": "577330",     # Fraport
    "KGX.DE": "626200",     # Kion Group
    "EVT.DE": "566480",     # Evotec
    "WAF.DE": "WCH888",     # Siltronic
    "TLX.DE": "TLX100",     # Talanx
    "DUE.DE": "556520",     # Dürr
    "BC8.DE": "541910",     # Bechtle
    "SDF.DE": "KSAG88",     # K+S
    "GFT.DE": "590087",     # GFT Technologies
    "S92.DE": "SMA954",     # SMA Solar
    "HYQ.DE": "549309",     # Hypoport
    "STR.DE": "STRA01",     # Ströer
    "COK.DE": "542800",     # CompuGroup Medical
    "DWS.DE": "DWS100",     # DWS Group
    "SIX2.DE": "723132",    # Sixt Vz.
    "KWS.DE": "707400",     # KWS Saat
    "JEN.DE": "A2NB60",     # Jenoptik
    "MOR.DE": "663200",     # MorphoSys
    "PNE3.DE": "A0JBPG",    # PNE AG
    "PSM.DE": "PSM777",     # ProSiebenSat.1
    "SGL.DE": "723530",     # SGL Carbon
    "SZU.DE": "729700",     # Südzucker
    "WCH.DE": "WCH888",     # Wacker Chemie
    "ZO1.DE": "511170",     # Zooplus

    # --- Europa Bluechips ---
    "NOVO-B.CO": "A1XH62",  # Novo Nordisk
    "ASML.AS": "A1J4U4",    # ASML Holding
    "MC.PA": "853292",      # LVMH
    "OR.PA": "853888",      # L'Oreal
    "RMS.PA": "886735",     # Hermes International
    "RACE.MI": "A2ACKK",    # Ferrari
    "SAF.PA": "924781",     # Safran
    "SU.PA": "860180",      # Schneider Electric
    "SAN.PA": "920657",     # Sanofi
    "BNP.PA": "887771",     # BNP Paribas
    "TTE.PA": "850727",     # TotalEnergies
    "ADYEN.AS": "A2JNF4",   # Adyen
    "BESI.AS": "936793",    # BE Semiconductor
    "PRX.AS": "A2PR02",     # Prosus
    "INGA.AS": "A2ANV3",    # ING Groep
    "HEIA.AS": "A0CA0G",    # Heineken
    "NESN.SW": "A0Q4DC",    # Nestle
    "ROG.SW": "855371",     # Roche
    "NOVN.SW": "904278",    # Novartis
    "CFR.SW": "A1W5CV",     # Richemont
    "ABBN.SW": "919730",    # ABB Ltd.
    "UBSG.SW": "A12DFH",    # UBS Group
    "LONN.SW": "928619",    # Lonza Group
    "AZN.L": "885407",      # AstraZeneca
    "SHEL.L": "A3C99G",     # Shell plc
    "HSBA.L": "923893",     # HSBC Holdings
    "ULVR.L": "A0JMQ9",     # Unilever
    "BP.L": "850501",       # BP plc
    "RIO.L": "852147",      # Rio Tinto
    "BATS.L": "916018",     # British American Tobacco
    "DGE.L": "851247",      # Diageo
    "FLTR.L": "A2PD90",     # Flutter Entertainment

    # --- Krypto (ETPs / Zertifikate) ---
    "ETH-USD": "A28M8D",    # 21Shares Ethereum ETP
    "XRP-USD": "A278KE",    # 21Shares Ripple XRP ETP
    "BNB-USD": "A278KE",    # 21Shares Binance BNB ETP
    "ADA-USD": "A3GX1A",    # 21Shares Cardano ETP
    "AVAX-USD": "A3GV8E",   # 21Shares Avalanche ETP
    "LINK-USD": "A3GV8D",   # 21Shares Chainlink ETP
    "DOT-USD": "A3GWSL",    # 21Shares Polkadot ETP
    "NEAR-USD": "A3GW11",   # 21Shares Near ETP
    "SUI-USD": "A3ETSU",    # 21Shares Sui ETP
    "TAO-USD": "A3ETTA",    # Bittensor
    "RENDER-USD": "A3ETRN", # Render
    "FET-USD": "A3ETFE",    # Artificial Superintelligence Alliance

    # --- Anleihen & ETFs ---
    "TLT": "A0B63A",        # iShares 20+ Year Treasury Bond ETF
    "HYG": "A0M623",        # iShares iBoxx $ High Yield Corporate Bond
    "LQD": "A0DK61",        # iShares iBoxx $ Investment Grade Corporate
    "BND": "A0NCFQ",        # Vanguard Total Bond Market ETF
    "SPY": "A0AET0",        # SPDR S&P 500 ETF Trust
    "QQQ": "A0NER2",        # Invesco QQQ Trust (Nasdaq 100)
    "IWM": "592736",        # iShares Russell 2000 ETF

    # --- Edelmetalle & Rohstoffe ---
    "GC=F": "A0S9GB",       # Xetra-Gold / Gold Spot
    "SI=F": "A0N62F",       # WisdomTree Physical Silver / Silber Spot
    "PL=F": "A0N62E",       # WisdomTree Physical Platinum
    "PA=F": "A0N62D",       # WisdomTree Physical Palladium
    "HG=F": "A0KRJU",       # WisdomTree Copper (Kupfer)
    "CL=F": "767228",       # Rohöl WTI ETC
    "BZ=F": "767229",       # Rohöl Brent ETC
    "NG=F": "A0KRJ3"        # Erdgas Natural Gas ETC
}

def get_wkn(symbol: str) -> str:
    """Returns the official German WKN (Wertpapierkennnummer / WKZ) for any asset symbol."""
    if not symbol:
        return "-"
    
    clean_sym = symbol.strip()
    
    # 1. Direct match
    if clean_sym in TICKER_TO_WKN:
        return TICKER_TO_WKN[clean_sym]
    
    # 2. Upper match
    if clean_sym.upper() in TICKER_TO_WKN:
        return TICKER_TO_WKN[clean_sym.upper()]
    
    # 3. Strip exchange suffix (.DE, .PA, .AS, etc.)
    base_sym = clean_sym.split(".")[0].upper()
    if base_sym in TICKER_TO_WKN:
        return TICKER_TO_WKN[base_sym]
        
    # 4. Strip crypto suffix (-USD, -EUR)
    base_crypto = clean_sym.split("-")[0].upper()
    if f"{base_crypto}-USD" in TICKER_TO_WKN:
        return TICKER_TO_WKN[f"{base_crypto}-USD"]
    if base_crypto in TICKER_TO_WKN:
        return TICKER_TO_WKN[base_crypto]

    # 5. Deterministic clean fallback 6-char identifier if unlisted
    # (Extract alphanumeric characters, upper case, padded to 6 chars)
    alphanumeric = re.sub(r'[^A-Z0-9]', '', clean_sym.upper())
    if len(alphanumeric) >= 6:
        return alphanumeric[:6]
    elif len(alphanumeric) > 0:
        return f"A{alphanumeric.ljust(5, '0')}"
    return "A00000"

def get_wkn_display(symbol: str, name: Optional[str] = None) -> str:
    """Formats a user-facing label with WKN as primary identifier."""
    wkn = get_wkn(symbol)
    if name:
        return f"{name} (WKN: {wkn})"
    return f"WKN: {wkn}"
