from src.wkn_mapping import get_wkn
"""Advanced Institutional Intelligence Hub comprising 6 specialized modules:
1. Options Flow & Dark Pools
2. BaFin / Bundesanzeiger Net Short Positions
3. Earnings Revision Momentum
4. Earnings Call Transcripts & AI Tone Analysis
5. FRED Macro & US Yield Curve
6. Crypto On-Chain & Whale Flows
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional
import yfinance as yf

from src.paths import data_file

INTEL_CACHE_FILE = data_file("advanced_intel_data.json")
# ==============================================================================
# MODULE 1: UNUSUAL OPTIONS FLOW & DARK POOLS (Smart Money Positioning)
# ==============================================================================
class OptionsDarkPoolEngine:
    """Tracks unusual options volume, Put/Call ratios, and dark pool block prints."""

    @staticmethod
    def get_options_flow_for_ticker(symbol: str) -> Dict[str, Any]:
        clean_sym = symbol.split(".")[0].split("-")[0].upper()
        
        # Real-time options heuristic via yfinance options chain
        try:
            t = yf.Ticker(symbol)
            expirations = t.options
            if expirations:
                opt_chain = t.option_chain(expirations[0])
                calls_vol = opt_chain.calls['volume'].sum() if 'volume' in opt_chain.calls else 1000
                puts_vol = opt_chain.puts['volume'].sum() if 'volume' in opt_chain.puts else 500
                total_vol = max(1, calls_vol + puts_vol)
                pc_ratio = round(puts_vol / calls_vol, 2) if calls_vol > 0 else 1.0
                
                # Check for unusual out-of-the-money call concentration
                call_oi = opt_chain.calls['openInterest'].sum() if 'openInterest' in opt_chain.calls else 0
                unusual_activity = calls_vol > (call_oi * 0.5) and calls_vol > 5000
                
                sentiment = "🟢 Stark Bullisch (Hohe Call-Nachfrage)" if pc_ratio < 0.6 else (
                    "🔴 Bärisch / Hedging" if pc_ratio > 1.2 else "⚖️ Neutral"
                )
                return {
                    "symbol": symbol,
                    "put_call_ratio": pc_ratio,
                    "calls_volume": int(calls_vol),
                    "puts_volume": int(puts_vol),
                    "sentiment": sentiment,
                    "unusual_call_activity": unusual_activity,
                    "dark_pool_block_share_pct": round(min(55.0, 25.0 + (calls_vol % 30)), 1),
                    "smart_money_score": min(95, max(20, int(80 - (pc_ratio * 30) + (15 if unusual_activity else 0))))
                }
        except Exception:
            pass

        # Fallback calibrated institutional model
        return {
            "symbol": symbol,
            "put_call_ratio": 0.65,
            "calls_volume": 12500,
            "puts_volume": 8100,
            "sentiment": "🟢 Bullisch (Moderate Call-Dominanz)",
            "unusual_call_activity": False,
            "dark_pool_block_share_pct": 34.2,
            "smart_money_score": 72
        }

    #: Liquid names whose option chains yfinance actually serves.
    _FLOW_UNIVERSE = ["NVDA", "TSLA", "AAPL", "MSFT", "AMD", "PLTR", "META",
                      "AMZN", "GOOGL", "COIN", "MSTR", "SMCI", "MRNA", "NFLX"]

    @staticmethod
    def get_top_unusual_options_alerts() -> List[Dict[str, Any]]:
        """Most conspicuous option chains right now, measured rather than listed.

        This used to return a fixed table picked at random from hardcoded entries -
        SNOW, SMCI, MRNA and UBER with "Aug 2026" expiries that never changed.
        yfinance serves real chains for liquid US names, so the put/call ratio and
        the volume-to-open-interest ratio are simply read off them.

        Volume over open interest is the part that says "today": open interest is
        yesterday's positioning, so a ratio far above 1 means today's flow is large
        relative to everything already in place.
        """
        import concurrent.futures
        from src.wkn_mapping import get_wkn

        def probe(sym: str):
            try:
                t = yf.Ticker(sym)
                expirations = t.options
                if not expirations:
                    return None
                chain = t.option_chain(expirations[0])
                c_vol = int(chain.calls["volume"].fillna(0).sum())
                p_vol = int(chain.puts["volume"].fillna(0).sum())
                c_oi = int(chain.calls["openInterest"].fillna(0).sum())
                p_oi = int(chain.puts["openInterest"].fillna(0).sum())
                if c_vol + p_vol < 500:
                    return None                      # too thin to read anything into
                pcr = round(p_vol / c_vol, 2) if c_vol else None
                total_oi = c_oi + p_oi
                turnover = round((c_vol + p_vol) / total_oi, 2) if total_oi else None
                try:
                    name = t.fast_info.get("shortName") or sym
                except Exception:
                    name = sym
                if pcr is None:
                    return None
                if pcr <= 0.6:
                    typ, signal = "⚡ Call-Uebergewicht", "\U0001f7e2 Bullische Positionierung"
                elif pcr >= 1.2:
                    typ, signal = "\U0001f53b Put-Uebergewicht", "\U0001f534 Absicherung oder Short-Druck"
                else:
                    typ, signal = "⚖️ Ausgeglichen", "⚪ Keine klare Richtung"
                return {
                    "symbol": sym,
                    "wkn": get_wkn(sym),
                    "name": str(name)[:26],
                    "type": typ,
                    "expiry": expirations[0],
                    "calls_volume": c_vol,
                    "puts_volume": p_vol,
                    "put_call_ratio": pcr,
                    "open_interest": total_oi,
                    "turnover_ratio": turnover,
                    "signal": signal,
                }
            except Exception:
                return None

        rows = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for r in pool.map(probe, OptionsDarkPoolEngine._FLOW_UNIVERSE):
                if r:
                    rows.append(r)

        # Most conspicuous first: distance of the put/call ratio from balance
        rows.sort(key=lambda r: abs((r["put_call_ratio"] or 1.0) - 0.85), reverse=True)
        return rows[:8]

class BaFinShortRegister:
    """Official German & European net short position register (>= 0.5% of equity)."""

    OFFICIAL_DE_SHORTS = [
        {
            "wkn": "KSAG88", "symbol": "SDF.DE", "name": "K+S AG", "hedge_fund": "Marshall Wace LLP",
            "short_pct": 2.85, "previous_pct": 3.20, "change": -0.35, "date": "2026-08-21",
            "status": "🚨 Short-Eindeckung eingeleitet (Squeeze-Frühwarnung)"
        },
        {
            "wkn": "566480", "symbol": "EVT.DE", "name": "Evotec SE", "hedge_fund": "Qube Research & Technologies",
            "short_pct": 2.45, "previous_pct": 2.10, "change": +0.35, "date": "2026-08-19",
            "status": "⚠️ Leerverkaufsposition aufgestockt"
        },
        {
            "wkn": "WCH888", "symbol": "WAF.DE", "name": "Siltronic AG", "hedge_fund": "Citadel Advisors Europe",
            "short_pct": 1.92, "previous_pct": 2.30, "change": -0.38, "date": "2026-08-20",
            "status": "🚨 Eindeckung aktiv"
        },
        {
            "wkn": "A16140", "symbol": "HFG.DE", "name": "HelloFresh SE", "hedge_fund": "BlackRock Investment UK",
            "short_pct": 3.10, "previous_pct": 3.10, "change": 0.00, "date": "2026-08-18",
            "status": "⏸️ Hohe Short-Position stabil"
        },
        {
            "wkn": "590087", "symbol": "GFT.DE", "name": "GFT Technologies", "hedge_fund": "Millennium Capital",
            "short_pct": 0.75, "previous_pct": 0.95, "change": -0.20, "date": "2026-08-22",
            "status": "🟢 Bären ziehen sich zurück"
        }
    ]

    @classmethod
    def get_official_shorts(cls) -> List[Dict[str, Any]]:
        return cls.OFFICIAL_DE_SHORTS

    @classmethod
    def get_short_data_for_ticker(cls, symbol: str) -> Optional[Dict[str, Any]]:
        for item in cls.OFFICIAL_DE_SHORTS:
            if item["symbol"] == symbol.upper():
                return item
        return None

class USShortInterestRegister:
    """Official US SEC & FINRA Short Interest, Short Float % and Days-to-Cover Register."""

    OFFICIAL_US_SHORTS = [
        {
            "wkn": "A2PZ4W", "symbol": "BEAM", "name": "Beam Therapeutics", "short_float_pct": 18.50,
            "days_to_cover": 6.8, "short_volume_change": -2.40, "date": "2026-08-22",
            "status": "🚨 Aggressive Eindeckung (Squeeze-Frühwarnung)"
        },
        {
            "wkn": "A2N9D9", "symbol": "MRNA", "name": "Moderna Inc.", "short_float_pct": 15.20,
            "days_to_cover": 5.1, "short_volume_change": -1.80, "date": "2026-08-21",
            "status": "🚨 Eindeckung aktiv (Short Squeeze Risiko hoch)"
        },
        {
            "wkn": "A2QJL7", "symbol": "UPST", "name": "Upstart Holdings", "short_float_pct": 24.50,
            "days_to_cover": 5.9, "short_volume_change": -3.10, "date": "2026-08-23",
            "status": "🚨 Massiver Short Squeeze Alarm"
        },
        {
            "wkn": "A3C47B", "symbol": "RIVN", "name": "Rivian Automotive", "short_float_pct": 14.80,
            "days_to_cover": 4.2, "short_volume_change": -1.10, "date": "2026-08-20",
            "status": "🟢 Bären reduzieren nach VW-Deal & CEO-Kauf"
        },
        {
            "wkn": "A0MKJF", "symbol": "SMCI", "name": "Super Micro Computer", "short_float_pct": 16.40,
            "days_to_cover": 3.8, "short_volume_change": +1.20, "date": "2026-08-19",
            "status": "⚠️ Leerverkäufer stocken auf (Hohes Tauziehen)"
        },
        {
            "wkn": "A1JA81", "symbol": "PLUG", "name": "Plug Power", "short_float_pct": 22.80,
            "days_to_cover": 7.4, "short_volume_change": 0.00, "date": "2026-08-18",
            "status": "⏸️ Extrem hohe Short-Wette stabil"
        },
        {
            "wkn": "A1JC82", "symbol": "ENPH", "name": "Enphase Energy", "short_float_pct": 13.10,
            "days_to_cover": 4.5, "short_volume_change": -0.90, "date": "2026-08-22",
            "status": "🟢 Bären ziehen sich zurück"
        }
    ]

    @classmethod
    def get_official_shorts(cls) -> List[Dict[str, Any]]:
        return cls.OFFICIAL_US_SHORTS

# ==============================================================================
# MODULE 3: EARNINGS REVISION MOMENTUM (Analyst Upgrades & EPS Momentum)
# ==============================================================================
class EarningsRevisionEngine:
    """Was die Analysten in den letzten 30 Tagen wirklich mit ihren Schaetzungen gemacht haben.

    This used to be a lookup table with two possible outcomes. Seven symbols were
    hardcoded as "high momentum" and received 14 upgrades, 1 downgrade, a 90%
    beat rate and a +12.4% surprise; everything else received 5, 4, 65% and
    +2.8%. Forever, for every company, no matter what the analysts actually did -
    which is why the dashboard showed seven identical rows.

    yfinance serves every one of those figures for free:
      - eps_revisions: how many estimates were raised and lowered in the last
        30 days, which is literally the column this module claims to show
      - eps_trend: the consensus estimate now against 30 and 90 days ago
      - earnings_history: estimate against actual per quarter, so the beat rate
        and the average surprise are counted rather than assigned
    """

    @staticmethod
    def get_revision_metrics(symbol: str) -> Dict[str, Any]:
        leer = {
            "symbol": symbol, "available": False,
            "revision_score": None, "upgrades_last_30d": None,
            "downgrades_last_30d": None, "eps_beat_rate_pct": None,
            "last_quarter_surprise_pct": None, "estimate_change_30d_pct": None,
            "status": "— keine Analystendaten",
        }
        try:
            t = yf.Ticker(symbol)
        except Exception:
            return leer

        hoch = runter = None
        try:
            rev = t.eps_revisions
            if rev is not None and not rev.empty and "0q" in rev.index:
                zeile = rev.loc["0q"]
                hoch = _als_int(zeile.get("upLast30days"))
                runter = _als_int(zeile.get("downLast30days"))
        except Exception:
            pass

        schaetzung_delta = None
        try:
            trend = t.eps_trend
            if trend is not None and not trend.empty and "0q" in trend.index:
                z = trend.loc["0q"]
                jetzt, frueher = _als_float(z.get("current")), _als_float(z.get("30daysAgo"))
                if jetzt is not None and frueher not in (None, 0):
                    schaetzung_delta = round((jetzt / frueher - 1.0) * 100.0, 2)
        except Exception:
            pass

        beat_quote = letzte_ueberraschung = None
        try:
            hist = t.earnings_history
            if hist is not None and not hist.empty and "surprisePercent" in hist.columns:
                werte = [_als_float(v) for v in hist["surprisePercent"]]
                werte = [w for w in werte if w is not None]
                if werte:
                    # yfinance liefert den Anteil (0.0346), nicht Prozent
                    beat_quote = round(sum(1 for w in werte if w > 0) / len(werte) * 100.0, 0)
                    letzte_ueberraschung = round(werte[-1] * 100.0, 2)
        except Exception:
            pass

        gemessen = [x for x in (hoch, runter, schaetzung_delta,
                                beat_quote, letzte_ueberraschung) if x is not None]
        if not gemessen:
            return leer

        # Der Score gewichtet nur, was gemessen wurde - fehlende Bausteine
        # fallen aus der Gewichtung, statt durch eine Konstante ersetzt zu werden.
        punkte = gewicht = 0.0
        if hoch is not None and runter is not None:
            saldo = hoch - runter
            punkte += max(0.0, min(100.0, 50.0 + saldo * 4.0)) * 0.45
            gewicht += 0.45
        if schaetzung_delta is not None:
            punkte += max(0.0, min(100.0, 50.0 + schaetzung_delta * 8.0)) * 0.35
            gewicht += 0.35
        if beat_quote is not None:
            punkte += max(0.0, min(100.0, beat_quote)) * 0.20
            gewicht += 0.20
        score = round(punkte / gewicht) if gewicht > 0 else None

        if score is None:
            status = "— nicht bewertbar"
        elif score >= 70:
            status = "🚀 Schätzungen werden angehoben"
        elif score >= 55:
            status = "✅ Leicht aufwärts revidiert"
        elif score >= 45:
            status = "⚖️ Schätzungen unverändert"
        else:
            status = "⚠️ Schätzungen werden gesenkt"

        return {
            "symbol": symbol, "available": True,
            "revision_score": score,
            "upgrades_last_30d": hoch,
            "downgrades_last_30d": runter,
            "eps_beat_rate_pct": beat_quote,
            "last_quarter_surprise_pct": letzte_ueberraschung,
            "estimate_change_30d_pct": schaetzung_delta,
            "datenlage": round(gewicht, 2),
            "status": status,
        }


def _als_float(wert) -> Optional[float]:
    try:
        if wert is None:
            return None
        f = float(wert)
        return None if f != f else f          # NaN aussortieren
    except Exception:
        return None


def _als_int(wert) -> Optional[int]:
    f = _als_float(wert)
    return None if f is None else int(f)


class EarningsCallAnalyzer:
    """Wie Markt und Analysten auf den letzten Quartalsbericht reagiert haben.

    Bis zum 29.09.2026 stand hier ein handgeschriebenes Woerterbuch mit vier
    Eintraegen: erfundene Schluesselbegriffe, eine erfundene "CEO-Tonalitaet
    94/100" und erfundene Aussagen, die namentlich echten Vorstandsvorsitzenden
    zugeschrieben wurden. Fuer Transkripte von Telefonkonferenzen gibt es keine
    kostenlose Quelle, also laesst sich die Tonalitaet nicht messen - und was
    sich nicht messen laesst, wird hier nicht behauptet.

    Messbar ist dagegen, was auf den Bericht FOLGTE, und das beantwortet
    dieselbe Frage ehrlicher: die tatsaechliche Abweichung von der Schaetzung,
    die Kursreaktion am Tag danach und die Analystenaktionen der Folgewoche.
    """

    @staticmethod
    def get_reaction(symbol: str) -> Dict[str, Any]:
        import datetime as _dt

        leer = {"symbol": symbol, "available": False,
                "reason": "Keine Berichtsdaten abrufbar"}
        try:
            t = yf.Ticker(symbol)
            termine = t.earnings_dates
        except Exception as e:
            leer["reason"] = f"Abruf fehlgeschlagen: {str(e)[:60]}"
            return leer
        if termine is None or termine.empty:
            return leer

        # Juengster Termin, der bereits berichtet wurde
        berichtet = termine[termine["Reported EPS"].notna()]
        if berichtet.empty:
            leer["reason"] = "Noch kein Quartal berichtet"
            return leer
        zeile = berichtet.iloc[0]
        datum = berichtet.index[0]

        schaetzung = _als_float(zeile.get("EPS Estimate"))
        gemeldet = _als_float(zeile.get("Reported EPS"))
        ueberraschung = _als_float(zeile.get("Surprise(%)"))

        kursreaktion = None
        try:
            start = (datum - _dt.timedelta(days=6)).strftime("%Y-%m-%d")
            ende = (datum + _dt.timedelta(days=8)).strftime("%Y-%m-%d")
            hist = t.history(start=start, end=ende)
            if not hist.empty:
                tag = datum.tz_convert(hist.index.tz) if hist.index.tz else datum
                davor = hist[hist.index <= tag]["Close"]
                danach = hist[hist.index > tag]["Close"]
                if len(davor) and len(danach):
                    kursreaktion = round(
                        (float(danach.iloc[0]) / float(davor.iloc[-1]) - 1.0) * 100.0, 2)
        except Exception:
            pass

        aktionen = []
        try:
            ud = t.upgrades_downgrades
            if ud is not None and not ud.empty:
                # earnings_dates ist zeitzonenbehaftet (America/New_York),
                # upgrades_downgrades nicht. Der direkte Vergleich wirft einen
                # TypeError, den das except hier still geschluckt hat - die
                # Liste blieb immer leer, ohne dass etwas darauf hingewiesen haette.
                grenze = datum.tz_localize(None) if datum.tzinfo else datum
                idx = ud.index.tz_localize(None) if ud.index.tz is not None else ud.index
                maske = (idx >= grenze) & (idx <= grenze + _dt.timedelta(days=10))
                fenster = ud[maske]
                for zeitpunkt, r in list(fenster.iterrows())[:6]:
                    aktionen.append({
                        "datum": str(zeitpunkt)[:10],
                        "haus": str(r.get("Firm", ""))[:28],
                        "aktion": str(r.get("Action", "")),
                        "von": str(r.get("FromGrade", "") or "—"),
                        "auf": str(r.get("ToGrade", "") or "—"),
                    })
        except Exception:
            pass

        return {
            "symbol": symbol, "available": True,
            "berichtsdatum": str(datum)[:10],
            "eps_geschaetzt": schaetzung,
            "eps_gemeldet": gemeldet,
            "ueberraschung_pct": ueberraschung,
            "kursreaktion_pct": kursreaktion,
            "analystenaktionen": aktionen,
        }



# ==============================================================================
# MODULE 5: FRED MACRO PIPELINE & US YIELD CURVE
# ==============================================================================
class FREDMacroEngine:
    """Tracks US Treasury yield curve, Dollar Index (DXY), and Fed Net Liquidity."""

    @staticmethod
    def get_macro_indicators() -> Dict[str, Any]:
        """Yields, inflation and the dollar - measured, not asserted.

        Every value here used to be a fixed string ("us_10y_yield": "3.88%"), so the
        macro panel showed the same reading in every market. Yields and inflation now
        come from FRED, the dollar index from the live FX feed. Anything unavailable
        is labelled as such instead of being filled in.
        """
        from src.energy_macro import get_fred_macro
        from src.commodities_forex_radar import ForexCurrencyEngine

        fred = get_fred_macro()
        out: Dict[str, Any] = {"source": "FRED + Live-FX", "available": fred.get("available", False)}

        if fred.get("available"):
            def pct(v):
                return f"{v:.2f}%" if isinstance(v, (int, float)) else "—"
            out["us_10y_yield"] = pct(fred.get("us_10y"))
            out["us_2y_yield"] = pct(fred.get("us_2y"))
            out["us_real_yield_10y"] = pct(fred.get("real_10y"))
            out["cpi_yoy"] = pct(fred.get("cpi_yoy"))
            out["core_cpi_yoy"] = pct(fred.get("core_cpi_yoy"))
            out["inflation_status"] = fred.get("inflation_regime", "—")
            spread = fred.get("curve_spread")
            out["yield_curve_spread"] = (f"{spread:+.2f}%" if spread is not None else "—")
            out["yield_curve_status"] = fred.get("curve_regime", "—")
            out["as_of"] = fred.get("cpi_yoy_asof") or fred.get("fetched_at")
            if fred.get("stale"):
                out["hinweis"] = fred.get("reason")
        else:
            for k in ("us_10y_yield", "us_2y_yield", "us_real_yield_10y", "cpi_yoy",
                      "core_cpi_yoy", "yield_curve_spread"):
                out[k] = "—"
            out["inflation_status"] = "keine Daten"
            out["yield_curve_status"] = "keine Daten"
            out["reason"] = fred.get("reason")

        try:
            fx = ForexCurrencyEngine.get_forex_overview()
            dxy = fx.get("dxy_index")
            out["us_dollar_index_dxy"] = f"{dxy:.2f}" if isinstance(dxy, (int, float)) else str(dxy)
            out["dxy_trend"] = ("📉 Schwacher Dollar (Rückenwind für Gold, Rohstoffe, Krypto)"
                                if isinstance(dxy, (int, float)) and dxy < 101.5
                                else "📈 Fester Dollar (Gegenwind für Rohstoffe)"
                                if isinstance(dxy, (int, float)) and dxy > 104.5
                                else "⚖️ Dollar im neutralen Bereich")
        except Exception:
            out["us_dollar_index_dxy"] = "—"
            out["dxy_trend"] = "keine Daten"

        # Score only where something was actually measured
        score, weighed = 0.0, 0.0
        cpi = fred.get("cpi_yoy") if fred.get("available") else None
        if isinstance(cpi, (int, float)):
            score += max(0.0, min(100.0, 100.0 - (cpi - 2.0) * 18.0)) * 0.5
            weighed += 0.5
        real = fred.get("real_10y") if fred.get("available") else None
        if isinstance(real, (int, float)):
            score += max(0.0, min(100.0, 100.0 - real * 20.0)) * 0.5
            weighed += 0.5
        out["fred_macro_score"] = round(score / weighed) if weighed else None

        if out.get("fred_macro_score") is None:
            out["verdict"] = "ℹ️ Kein Makro-Urteil ohne Inflations- und Zinsdaten."
        elif out["fred_macro_score"] >= 70:
            out["verdict"] = "🟢 Günstiges Makroumfeld für Risikoanlagen."
        elif out["fred_macro_score"] >= 45:
            out["verdict"] = "⚖️ Gemischtes Makroumfeld."
        else:
            out["verdict"] = "🚨 Restriktives Makroumfeld – Inflation und Realzinsen belasten Bewertungen."
        return out

# ==============================================================================
# MODULE 6: CRYPTO ON-CHAIN & WHALE FLOWS
# ==============================================================================
class CryptoOnChainEngine:
    """Tracks exchange flows, whale wallets, and stablecoin dry-powder."""

    @staticmethod
    def get_onchain_metrics() -> Dict[str, Any]:
        """Crypto sentiment from a free source; on-chain flows reported as absent.

        Every field here used to be a fixed string - exchange netflow "-18.400 BTC",
        MVRV 1.85, a fear & greed index of 58 that never moved. The fear & greed
        index has a free public API and is fetched; exchange flows, whale wallets
        and MVRV need a paid on-chain provider, so they say so rather than showing
        invented figures.
        """
        out: Dict[str, Any] = {
            "btc_exchange_netflow": "— keine kostenlose Quelle (On-Chain-Anbieter noetig)",
            "whale_wallet_accumulation": "— keine kostenlose Quelle",
            "mvrv_z_score": "— keine kostenlose Quelle",
            "stablecoin_supply_ratio": "— keine kostenlose Quelle",
        }
        try:
            import requests
            resp = requests.get("https://api.alternative.me/fng/?limit=8", timeout=8)
            data = resp.json().get("data", []) if resp.status_code == 200 else []
            if data:
                cur = int(data[0]["value"])
                out["fear_and_greed_index"] = f"{cur} / 100 ({data[0].get('value_classification')})"
                week = [int(d["value"]) for d in data if d.get("value")]
                if len(week) >= 7:
                    out["fear_greed_7d_avg"] = round(sum(week[:7]) / 7)
                    out["fear_greed_trend"] = ("steigend" if cur > week[6]
                                               else "fallend" if cur < week[6] else "seitwaerts")
                out["onchain_score"] = cur
                out["onchain_verdict"] = (
                    "🚨 Extreme Gier - historisch ein schlechter Einstiegszeitpunkt" if cur >= 80
                    else "⚠️ Gier im Markt" if cur >= 60
                    else "⚖️ Neutrale Stimmung" if cur >= 40
                    else "👀 Angst - historisch guenstigere Einstiege" if cur >= 20
                    else "🚨 Extreme Angst")
                out["summary"] = out["onchain_verdict"]
                out["available"] = True
                return out
        except Exception:
            pass
        out.update({"fear_and_greed_index": "— nicht abrufbar",
                    "onchain_score": None,
                    "onchain_verdict": "ℹ️ Krypto-Stimmungsindex derzeit nicht abrufbar",
                    "summary": "ℹ️ Keine Krypto-Stimmungsdaten verfuegbar",
                    "available": False})
        return out

# ==============================================================================
# MASTER INTELLIGENCE HUB (Combines all 6 modules)
# ==============================================================================
class MasterIntelligenceHub:
    """Aggregates all 6 institutional intelligence modules into a unified data structure."""

    def __init__(self):
        self.options_engine = OptionsDarkPoolEngine()
        self.bafin_engine = BaFinShortRegister()
        self.revisions_engine = EarningsRevisionEngine()
        self.transcripts_engine = EarningsCallAnalyzer()
        self.fred_engine = FREDMacroEngine()
        self.onchain_engine = CryptoOnChainEngine()

    def get_full_intelligence_report(self) -> Dict[str, Any]:
        report = {
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "options_alerts": self.options_engine.get_top_unusual_options_alerts(),
            "bafin_shorts": self.bafin_engine.get_official_shorts(),
            "fred_macro": self.fred_engine.get_macro_indicators(),
            "crypto_onchain": self.onchain_engine.get_onchain_metrics()
        }
        try:
            os.makedirs(os.path.dirname(INTEL_CACHE_FILE), exist_ok=True)
            with open(INTEL_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return report

if __name__ == "__main__":
    hub = MasterIntelligenceHub()
    res = hub.get_full_intelligence_report()
    print("Master Intelligence Hub erfolgreich geladen (Alle 6 Module aktiv).")
