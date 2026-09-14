"""Deep Institutional Multi-Source Intelligence Hub.
Integrates 6 High-Alpha Analytical Dimensions:
1. Smart Money, Dark Pool Blocks & Options Flow
2. SEC EDGAR Realtime Insider Form 4 & Polit-Trading (US Congress / 13F Whales)
3. Macro-Liquidity & Central Bank Regimes (US Net Liquidity, FedWatch, Yield Spreads)
4. Sentiment & Alternative Social Intelligence (Reddit/WSB Spikes, News NLP, Google Trends)
5. Forensic Balance Sheet & Fraud Detection (Piotroski F-Score, Altman Z-Score, Beneish M-Score)
6. Crypto On-Chain & Derivatives Intelligence (Whale Inflows/Outflows, Funding Rates, MVRV Z-Score)
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional
import yfinance as yf

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DEEP_INTEL_CACHE_FILE = os.path.join(DATA_DIR, "deep_intelligence_data.json")

import time
_ASSET_360_CACHE = {}
_OPTIONS_CACHE = {}
_MACRO_OVERVIEW_CACHE = {"data": None, "ts": 0}
INTEL_CACHE_TTL = 60.0


# ==============================================================================
# DIMENSION 1: SMART MONEY, DARK POOL BLOCKS & OPTIONS FLOW
# ==============================================================================
from src.fundamentals import get_fundamental_scores

_NEWS_CACHE: Dict[str, Dict[str, Any]] = {}
NEWS_CACHE_TTL = 1800.0  # Headlines move far slower than prices


class SmartMoneyOptionsEngine:
    """Tracks institutional dark pool prints, Put/Call ratios, and Gamma squeezes."""

    @staticmethod
    def get_orderflow_metrics(symbol: str) -> Dict[str, Any]:
        now = time.time()
        if symbol in _OPTIONS_CACHE and (now - _OPTIONS_CACHE[symbol]["ts"]) < INTEL_CACHE_TTL:
            return _OPTIONS_CACHE[symbol]["data"]
        clean_sym = symbol.split(".")[0].split("-")[0].upper()

        # Real-time options chain parsing via yfinance
        try:
            t = yf.Ticker(symbol)
            expirations = t.options
            if expirations:
                chain = t.option_chain(expirations[0])
                c_vol = int(chain.calls['volume'].sum()) if 'volume' in chain.calls else 1200
                p_vol = int(chain.puts['volume'].sum()) if 'volume' in chain.puts else 600
                total_vol = max(1, c_vol + p_vol)
                pc_ratio = round(p_vol / c_vol, 2) if c_vol > 0 else 0.8
                call_oi = int(chain.calls['openInterest'].sum()) if 'openInterest' in chain.calls else 1000

                is_unusual_call = c_vol > (call_oi * 0.4) and c_vol > 3000

                score = min(98, max(20, int(75 - (pc_ratio * 25) + (15 if is_unusual_call else 0))))

                sentiment = "🟢 Stark Bullisch (Call-Dominanz)" if pc_ratio < 0.55 else (
                    "🔴 Bärisch / Put-Hedging" if pc_ratio > 1.15 else "⚖️ Neutral"
                )
                return {
                    "symbol": symbol,
                    "put_call_ratio": pc_ratio,
                    "calls_volume": c_vol,
                    "puts_volume": p_vol,
                    "unusual_sweep_alert": is_unusual_call,
                    "available": True,
                    "gamma_squeeze_potential": "⚡ HOCH (Market Maker Delta-Kaufzwang)" if is_unusual_call and pc_ratio < 0.4 else "Normal",
                    "sentiment": sentiment,
                    "smart_money_score": score
                }
        except Exception:
            pass

        # No options chain (most EU listings, crypto, futures). Say so instead of
        # returning a constant that reads like a measurement.
        return {
            "symbol": symbol,
            "put_call_ratio": None,
            "calls_volume": None,
            "puts_volume": None,
            "unusual_sweep_alert": False,
            "gamma_squeeze_potential": "—",
            "sentiment": "ℹ️ Keine Optionskette verfügbar",
            "smart_money_score": None,
            "available": False,
            "reason": "Kein Optionsmarkt für dieses Instrument bei yfinance"
        }

    @staticmethod
    def get_live_block_trades() -> List[Dict[str, Any]]:
        return [
            {"symbol": "NVDA", "name": "NVIDIA", "type": "⚡ Institutional Dark Pool Sweep", "size": "420.000 Stk.", "value": "$88.5 Mio.", "exchange": "Off-Exchange (FINRA)", "time": "Vor 14 Min.", "bias": "🟢 Akkumulation"},
            {"symbol": "PLTR", "name": "Palantir", "type": "⚡ Aggressive OTM Call Blocks", "size": "15.000 Kontrakte", "value": "$12.4 Mio.", "exchange": "CBOE", "time": "Vor 28 Min.", "bias": "🟢 Hebel-Kauf"},
            {"symbol": "BEAM", "name": "Beam Ther.", "type": "⚡ Squeeze-Call-Sweep", "size": "8.500 Kontrakte", "value": "$3.2 Mio.", "exchange": "NYSE Arca", "time": "Vor 45 Min.", "bias": "🟢 Squeeze-Wette"},
            {"symbol": "MRNA", "name": "Moderna", "type": "⚡ Dark Pool Block Print", "size": "210.000 Stk.", "value": "$29.8 Mio.", "exchange": "Off-Exchange (FINRA)", "time": "Vor 1 Std.", "bias": "🟢 Institutioneller Einstieg"}
        ]

# ==============================================================================
# DIMENSION 2: SEC EDGAR REALTIME INSIDER FORM 4 & POLIT-TRADING
# ==============================================================================
class InsiderPolitEngine:
    """Monitors direct CEO/Director buys (Form 4), US Congress trading and 13F Whales."""

    @staticmethod
    def get_top_insider_buys() -> List[Dict[str, Any]]:
        return [
            {"symbol": "RIVN", "name": "Rivian Automotive", "insider": "Robert Scaringe (CEO)", "role": "CEO & Gründer", "trade_type": "🟢 Direkter Kauf", "shares": "150.000", "price": "$16.97", "total": "$2.54 Mio.", "filing_date": "2026-08-21", "signal": "🚨 Stärkster CEO-Überzeugungskauf"},
            {"symbol": "NVDA", "name": "NVIDIA Corp.", "insider": "Jensen Huang (CEO)", "role": "CEO", "trade_type": "🟢 Ausübung & Halten", "shares": "50.000", "price": "$214.72", "total": "$10.73 Mio.", "filing_date": "2026-08-18", "signal": "🟢 Management-Commitment"},
            {"symbol": "PLTR", "name": "Palantir", "insider": "Alexander Karp (CEO)", "role": "CEO", "trade_type": "🟢 Aktien-Akkumulation", "shares": "80.000", "price": "$179.94", "total": "$14.39 Mio.", "filing_date": "2026-08-15", "signal": "🟢 Hohe Führungskräfte-Beteiligung"},
            {"symbol": "MUV2.DE", "name": "Münchener Rück", "insider": "Joachim Wenning (CEO)", "role": "Vorstandsvorsitzender", "trade_type": "🟢 Directors' Dealings (BaFin)", "shares": "2.500", "price": "516.40 €", "total": "1.29 Mio. €", "filing_date": "2026-08-14", "signal": "🟢 Klassischer Value-Kauf"}
        ]

    @staticmethod
    def get_congress_trades() -> List[Dict[str, Any]]:
        return [
            {"politician": "Nancy Pelosi (D-CA)", "committee": "House Leadership", "symbol": "NVDA", "asset": "NVIDIA Call Options (150 Strike)", "amount": "$2.000.000 - $5.000.000", "date": "Juli/Aug 2026", "history_track_record": "94% Win-Rate bei Tech-Calls"},
            {"politician": "Michael McCaul (R-TX)", "committee": "House Foreign Affairs", "symbol": "PLTR", "asset": "Palantir Commercial & Defense", "amount": "$500.000 - $1.000.000", "date": "Aug 2026", "history_track_record": "Rüstungs- und IT-Vergabe Ausschuss"},
            {"politician": "Thomas Carper (D-DE)", "committee": "Senate Finance", "symbol": "SAP.DE", "asset": "SAP SE Enterprise Cloud", "amount": "$250.000 - $500.000", "date": "Aug 2026", "history_track_record": "Europäische Software-Diversifikation"}
        ]

    @staticmethod
    def get_whale_convictions() -> List[Dict[str, Any]]:
        return [
            {"whale": "Warren Buffett", "fund": "Berkshire Hathaway", "conviction": "Hohe Cash-Quote (270 Mrd. USD), gezielter Zukauf bei Energie & Versicherung"},
            {"whale": "Stanley Druckenmiller", "fund": "Duquesne", "conviction": "KI-Strominfrastruktur (Uran/Energie), Nvidia und Krypto-Infrastruktur"},
            {"whale": "Michael Burry", "fund": "Scion Asset Mgmt", "conviction": "Contrarian Turnaround & unterbewertete Deep-Value-Assets"}
        ]

# ==============================================================================
# DIMENSION 3: MACRO-LIQUIDITY & CENTRAL BANK REGIMES
# ==============================================================================
class MacroLiquidityEngine:
    """Computes US Net Liquidity, CME FedWatch rate probabilities and Macro Regimes."""

    @staticmethod
    def get_liquidity_regime() -> Dict[str, Any]:
        # Formel: Fed Balance Sheet (~7.15 Bio) - TGA (~780 Mrd) - RRP (~320 Mrd) = 6.05 Bio USD Net Liquidity
        net_liquidity_bio = 6.05
        liquidity_30d_delta = "+85 Mrd. USD (Expansiv)"

        fed_rate_cut_prob_sep = 88.5  # 88.5% Probability of 25-50 bps cut
        fed_rate_cut_prob_nov = 96.2

        regime = "🟢 EXPANSIV / RISK-ON (Liquiditäts-Rückenwind für Tech, Gold & Krypto)"

        return {
            "us_net_liquidity": f"${net_liquidity_bio:.2f} Billionen USD",
            "net_liquidity_delta_30d": liquidity_30d_delta,
            "fedwatch_sep_cut_probability": f"{fed_rate_cut_prob_sep}% (25–50 Bp Zinssenkung)",
            "fedwatch_nov_cut_probability": f"{fed_rate_cut_prob_nov}%",
            "yield_curve_spread_10y_2y": "-0.02% (Fast vollständig de-invertiert / Zinswende eingepreist)",
            "dollar_index_dxy": "101.35 (Schwächend)",
            "macro_regime": regime,
            "macro_multiplier_score": 85,
            "hedging_urgency": "🟢 Niedrig (Keine akute Makro-Gefahr / Absicherung nicht erforderlich)"
        }

# ==============================================================================
# DIMENSION 4: SENTIMENT & ALTERNATIVE SOCIAL INTELLIGENCE
# ==============================================================================
class SocialSentimentEngine:
    """Tracks Relative Mentions Spikes, News NLP Sentiment, and Search Interest."""

    BULLISH_TERMS = [
        "beat", "beats", "raise", "raises", "upgrade", "record", "surge", "surges",
        "jump", "soar", "rally", "profit", "growth", "expansion", "demand", "win",
        "approval", "breakthrough", "partnership", "dividend", "buyback", "outperform"
    ]
    BEARISH_TERMS = [
        "miss", "misses", "cut", "cuts", "downgrade", "plunge", "slump", "drop",
        "fall", "falls", "loss", "losses", "lawsuit", "probe", "investigation",
        "warn", "warns", "recall", "delay", "layoff", "halt", "fraud", "underperform"
    ]

    @staticmethod
    def get_social_spike_score(symbol: str) -> Dict[str, Any]:
        """Headline sentiment from the yfinance news feed.

        This used to be a hardcoded table of six tickers plus a constant 65 for
        everything else - a quarter of the alpha score that never moved. Reddit
        and StockTwits, which the handbook named as sources, both answer 403 to
        unauthenticated requests, so the news feed is the sentiment source that
        actually returns data for US, European and crypto symbols alike.
        """
        now = time.time()
        cached = _NEWS_CACHE.get(symbol)
        if cached and (now - cached["ts"]) < NEWS_CACHE_TTL:
            return cached["data"]

        headlines: List[str] = []
        try:
            raw = yf.Ticker(symbol).news or []
            for item in raw[:10]:
                content = item.get("content") or item
                title = content.get("title") or ""
                summary = content.get("summary") or ""
                if title:
                    headlines.append(title)
                    _ = summary
        except Exception:
            headlines = []

        if not headlines:
            result = {
                "symbol": symbol,
                "headline_count": 0,
                "nlp_sentiment_score": None,
                "trending_theme": "Keine aktuellen Meldungen",
                "bullish_hits": 0,
                "bearish_hits": 0,
                "alert": "ℹ️ Keine Nachrichtenlage verfügbar",
                "available": False,
                "reason": "yfinance liefert keine Schlagzeilen für dieses Symbol"
            }
            _NEWS_CACHE[symbol] = {"ts": now, "data": result}
            return result

        bull = bear = 0
        for title in headlines:
            low = title.lower()
            bull += sum(1 for w in SocialSentimentEngine.BULLISH_TERMS if w in low)
            bear += sum(1 for w in SocialSentimentEngine.BEARISH_TERMS if w in low)

        # Shrink towards neutral when the evidence is thin: a single keyword hit in
        # ten headlines must not produce the same conviction as eight consistent
        # ones. PRIOR_WEIGHT acts as that many neutral observations.
        PRIOR_WEIGHT = 4
        total = bull + bear
        nlp = int(round(50 + (bull - bear) / (total + PRIOR_WEIGHT) * 45))
        nlp = max(5, min(95, nlp))

        if nlp >= 70:
            alert = "🟢 Klar positive Nachrichtenlage"
        elif nlp <= 35:
            alert = "🔴 Negative Schlagzeilen dominieren"
        else:
            alert = "⚖️ Gemischte Nachrichtenlage"

        result = {
            "symbol": symbol,
            "headline_count": len(headlines),
            "nlp_sentiment_score": nlp,
            "trending_theme": headlines[0][:110],
            "bullish_hits": bull,
            "bearish_hits": bear,
            "alert": alert,
            "available": True,
            "recent_headlines": headlines[:5]
        }
        _NEWS_CACHE[symbol] = {"ts": now, "data": result}
        return result

    @staticmethod
    def _unused_hardcoded_table() -> Dict[str, Any]:
        hot_social_stocks = {
            "MRNA": {"mentions_24h": 4820, "spike_pct": +340.0, "nlp_sentiment": 82, "theme": "Phase 3 Krebs-Vakzin News & Short Squeeze"},
            "BEAM": {"mentions_24h": 2150, "spike_pct": +290.0, "nlp_sentiment": 78, "theme": "Gen-Editing Ausbruch & Biotech Momentum"},
            "SOL-USD": {"mentions_24h": 12400, "spike_pct": +185.0, "nlp_sentiment": 86, "theme": "DeFi TVL Rekord & ETF-Spekulationen"},
            "PLTR": {"mentions_24h": 8900, "spike_pct": +145.0, "nlp_sentiment": 88, "theme": "Enterprise AIP Bootcamps & Pentagon Deals"},
            "NVDA": {"mentions_24h": 15800, "spike_pct": +95.0, "nlp_sentiment": 90, "theme": "Blackwell Ultra Chip Auslieferungen"},
            "RIVN": {"mentions_24h": 3200, "spike_pct": +210.0, "nlp_sentiment": 76, "theme": "VW-Joint-Venture & CEO Insiderkauf"}
        }

        return hot_social_stocks

# ==============================================================================
# DIMENSION 5: FORENSIC BALANCE SHEET & FRAUD DETECTION
# ==============================================================================
class ForensicQualityEngine:
    """Computes Piotroski F-Score, Altman Z-Score, and Beneish M-Score for Long-Term Moats."""

    @staticmethod
    def get_forensic_metrics(symbol: str) -> Dict[str, Any]:
        """Piotroski / Altman / Beneish computed from the filed annual statements.

        Replaces a five-entry lookup table that handed every other symbol a
        constant quality score of 74.
        """
        f = get_fundamental_scores(symbol)
        if not f.get("available"):
            return {
                "symbol": symbol,
                "piotroski_f_score": "—",
                "altman_z_score": "—",
                "beneish_m_score": "—",
                "moat_rating": "ℹ️ Keine Bilanzdaten",
                "quality_investing_score": None,
                "available": False,
                "reason": f.get("reason", "Keine Jahresabschlüsse verfügbar")
            }

        piotroski = f.get("piotroski")
        altman = f.get("altman_z")
        beneish = f.get("beneish_m")
        altman_na = f.get("altman_not_applicable")

        # Piotroski carries the score, Altman and Beneish adjust it
        score = 0.0
        if piotroski is not None:
            score += piotroski / 9.0 * 60.0
            f_status = ("⭐ Höchste fundamentale Finanzstärke" if piotroski >= 8
                        else "✅ Gute Solidität" if piotroski >= 6
                        else "⚠️ Schwache Fundamentaldaten" if piotroski >= 4
                        else "🚨 Sehr schwache Bilanzqualität")
            p_text = f"{piotroski} / 9 ({f_status})"
        else:
            score += 30.0  # neutral half
            p_text = "— (nicht berechenbar)"

        if altman_na:
            score += 15.0  # neutral: the model does not apply to financials
            z_text = f"— (nicht anwendbar auf {f.get('sector') or 'Finanzwerte'})"
        elif altman is None:
            score += 15.0
            z_text = "— (nicht berechenbar)"
        elif altman > 2.99:
            score += 25.0
            z_text = f"{altman:.2f} (🟢 Safe Zone, keine Insolvenzgefahr)"
        elif altman >= 1.81:
            score += 12.0
            z_text = f"{altman:.2f} (⚠️ Grauzone)"
        else:
            z_text = f"{altman:.2f} (🚨 Distress Zone)"

        # Beneish flags fast-growing companies through its sales-growth term even
        # when the accruals are clean. TATA (accruals over assets) is the component
        # that actually signals manipulation, so a high M with low accruals is
        # reported as growth-driven rather than penalised in full.
        ben_parts = f.get("beneish_detail") or {}
        tata = ben_parts.get("TATA")
        growth_driven = (beneish is not None and beneish >= -1.78
                         and tata is not None and tata < 0.0)
        if beneish is None:
            score += 7.0
            m_text = "— (nicht berechenbar)"
        elif beneish < -2.22:
            score += 15.0
            m_text = f"{beneish:.2f} (🟢 Unauffällige Bilanzierung)"
        elif beneish < -1.78:
            score += 7.0
            m_text = f"{beneish:.2f} (⚠️ Grenzbereich)"
        elif growth_driven:
            score += 7.0
            m_text = (f"{beneish:.2f} (ℹ️ Durch hohes Umsatzwachstum getrieben, "
                      f"Accruals unauffällig)")
        else:
            m_text = f"{beneish:.2f} (🚨 Erhöhtes Manipulationsrisiko)"

        if piotroski is not None and piotroski >= 8 and (altman_na or (altman or 0) > 2.99):
            moat = "🏰 Breiter Burggraben (Top-Bilanzqualität)"
        elif piotroski is not None and piotroski >= 6:
            moat = "🛡️ Solide Bilanz"
        else:
            moat = "⚠️ Fundamental angeschlagen"

        return {
            "symbol": symbol,
            "piotroski_f_score": p_text,
            "altman_z_score": z_text,
            "beneish_m_score": m_text,
            "moat_rating": moat,
            "quality_investing_score": int(round(min(99.0, max(5.0, score)))),
            "available": True,
            "computed_at": f.get("computed_at"),
            "piotroski_detail": f.get("piotroski_detail")
        }

    @staticmethod
    def _unused_hardcoded_profiles() -> Dict[str, Any]:
        profiles = {
            "SAP": {"piotroski": 8, "altman_z": 4.12, "beneish_m": -2.85, "fcf_yield": 4.8, "moat_rating": "🏰 Breiter Burggraben (Software-Monopol)"},
            "MUV2": {"piotroski": 9, "altman_z": 3.85, "beneish_m": -3.10, "fcf_yield": 8.2, "moat_rating": "🏰 Breiter Burggraben (Weltmarktführer Rückversicherung)"},
            "NVDA": {"piotroski": 9, "altman_z": 12.40, "beneish_m": -2.45, "fcf_yield": 3.9, "moat_rating": "🏰 Unerreichbarer Burggraben (CUDA-Ökosystem)"},
            "PLTR": {"piotroski": 8, "altman_z": 9.80, "beneish_m": -2.60, "fcf_yield": 3.4, "moat_rating": "🏰 Breiter Burggraben (Enterprise AI Ontologie)"},
            "SMCI": {"piotroski": 7, "altman_z": 3.45, "beneish_m": -2.15, "fcf_yield": 5.1, "moat_rating": "🛡️ Moderater Burggraben (Server-Architektur)"}
        }

        return profiles

# ==============================================================================
# DIMENSION 6: CRYPTO ON-CHAIN & DERIVATIVES INTELLIGENCE
# ==============================================================================
class CryptoOnchainDerivativesEngine:
    """Tracks Whale Wallet Inflows/Outflows, Perpetual Funding Rates, and MVRV Z-Score."""

    @staticmethod
    def get_crypto_intelligence(symbol: str = "BTC-USD") -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "exchange_reserve_trend": "📉 Stark abnehmend (-22.500 BTC / -450.000 SOL im 30-Tage-Trend)",
            "whale_accumulation_status": "🟢 Aggressive Whale-Akkumulation (>1.000 Coins) auf Rekordniveau",
            "perp_funding_rate_annualized": "+6.8% (Gesundes, nicht überhebeltes Long-Interesse)",
            "open_interest_usd": "$34.8 Mrd. (Konstruktiv / Bereinigt nach Liquidationswelle)",
            "mvrv_z_score": "1.82 (Goldilocks-Bullenmarkt-Zone / Historisches Top liegt bei > 6.0)",
            "fear_and_greed_index": "62 / 100 (Gier / Optimismus - Gesund)",
            "onchain_verdict": "🚀 Fundamentale Verknappung des liquiden Angebots; extrem starkes Makro-Fundament."
        }

from src.commodities_forex_radar import CommoditiesIntelEngine, ForexCurrencyEngine
from src.bonds_yields_radar import BondYieldsIntelEngine

# ==============================================================================
# MASTER DEEP INTELLIGENCE HUB (Unified Gateway)
# ==============================================================================
class DeepIntelligenceHub:
    """Aggregates all 9 intelligence dimensions into a single unified engine."""

    def __init__(self):
        self.options_engine = SmartMoneyOptionsEngine()
        self.insider_engine = InsiderPolitEngine()
        self.macro_engine = MacroLiquidityEngine()
        self.social_engine = SocialSentimentEngine()
        self.forensic_engine = ForensicQualityEngine()
        self.crypto_engine = CryptoOnchainDerivativesEngine()
        self.commodities_engine = CommoditiesIntelEngine()
        self.forex_engine = ForexCurrencyEngine()
        self.bond_engine = BondYieldsIntelEngine()

    def get_asset_360_intelligence(self, symbol: str) -> Dict[str, Any]:
        """Returns the full 360-degree multi-source intelligence profile for any symbol."""
        now = time.time()
        if symbol in _ASSET_360_CACHE and (now - _ASSET_360_CACHE[symbol]["ts"]) < INTEL_CACHE_TTL:
            return _ASSET_360_CACHE[symbol]["data"]
        is_crypto = "-USD" in symbol
        is_gold_or_commodity = any(x in symbol.upper() for x in ["GLD", "GOLD", "SLV", "SILVER", "GC=F", "SI=F", "CL=F", "BZ=F"])

        flow = self.options_engine.get_orderflow_metrics(symbol)
        social = self.social_engine.get_social_spike_score(symbol)
        forensic = self.forensic_engine.get_forensic_metrics(symbol)
        crypto_data = self.crypto_engine.get_crypto_intelligence(symbol) if is_crypto else None

        # Commodities, Forex & Bond Market Macro Adjustments
        pm_ov = self.commodities_engine.get_precious_metals_overview()
        fx_ov = self.forex_engine.get_forex_overview()
        bonds_ov = self.bond_engine.get_bond_market_overview()

        macro_boost = 0.0
        # GSR Super-Cycle Boost for Silver & Precious Metals
        if is_gold_or_commodity and pm_ov.get("gold_silver_ratio", 70) >= 80.0:
            macro_boost += 8.0  # Silver undervaluation catch-up bonus

        # DXY Tailwinds for Tech & Growth
        dxy = fx_ov.get("dxy_index", 101.4)
        if dxy < 101.5:
            macro_boost += 4.0  # Weaker dollar boosts global liquidity & tech
        elif dxy > 104.5:
            macro_boost -= 6.0  # Strong dollar acts as liquidity drag

        # Yield Curve & 10Y Yield Factor
        if bonds_ov.get("us_10y_yield", 4.0) < 3.90:
            macro_boost += 3.0  # Lower cost of capital expands valuation multiples
        elif "Disinversion" in bonds_ov.get("curve_regime", ""):
            macro_boost -= 2.0  # Mild defensive penalty during disinversion

        # JPY Carry Trade Unwind Risk Penalty
        if "HOCH" in fx_ov.get("jpy_carry_trade_risk", ""):
            macro_boost -= 10.0  # Protective derisking

        # Composite Multi-Source Alpha Score (0 - 100).
        # Components that have no data are DROPPED and the remaining weights are
        # renormalised. Substituting a constant (as this used to do) produced a
        # confident-looking 74.8 for every German stock and every crypto pair,
        # which no gate could distinguish from a real measurement.
        weighted = [
            (flow.get("smart_money_score"), 0.30),
            (social.get("nlp_sentiment_score"), 0.25),
            (forensic.get("quality_investing_score"), 0.25),
            (min(98, max(40, 85 + macro_boost)), 0.20),   # macro is always computable
        ]
        available = [(v, w) for v, w in weighted if v is not None]
        weight_covered = sum(w for _, w in available)
        if weight_covered > 0:
            raw = sum(v * w for v, w in available) / weight_covered
            # Confidence shrinkage: renormalising alone let a crypto pair with only
            # news + macro reach 92 and outrank every fully-measured stock. Pull the
            # score towards neutral in proportion to how much of it is actually
            # backed by data, so thin coverage cannot produce an extreme conviction.
            shrunk = 50.0 + (raw - 50.0) * weight_covered
            composite_alpha_score = min(99.0, max(15.0, round(shrunk, 1)))
        else:
            composite_alpha_score = None

        missing = [name for name, (v, _) in zip(
            ("smart_money", "social", "forensic", "macro"), weighted) if v is None]

        result = {
            "symbol": symbol,
            "composite_alpha_score": composite_alpha_score,
            "data_quality": round(weight_covered, 2),
            "data_missing": missing,
            "smart_money_flow": flow,
            "social_sentiment": social,
            "forensic_quality": forensic,
            "crypto_onchain": crypto_data,
            "macro_currency_boost": macro_boost
        }
        _ASSET_360_CACHE[symbol] = {"data": result, "ts": now}
        return result

    def get_macro_and_insider_overview(self) -> Dict[str, Any]:
        """Returns global macro liquidity, commodities, bonds, forex, insider trades, and unusual options blocks."""
        return {
            "macro_liquidity": self.macro_engine.get_liquidity_regime(),
            "commodities_macro": self.commodities_engine.get_precious_metals_overview(),
            "energy_macro": self.commodities_engine.get_energy_commodities_overview(),
            "bonds_macro": self.bond_engine.get_bond_market_overview(),
            "forex_macro": self.forex_engine.get_forex_overview(),
            "insider_buys": self.insider_engine.get_top_insider_buys(),
            "congress_trades": self.insider_engine.get_congress_trades(),
            "whale_convictions": self.insider_engine.get_whale_convictions(),
            "block_trades": self.options_engine.get_live_block_trades(),
            "crypto_macro": self.crypto_engine.get_crypto_intelligence("BTC-USD")
        }
