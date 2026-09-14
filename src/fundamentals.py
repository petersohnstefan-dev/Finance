"""Real forensic accounting metrics computed from filed financial statements.

Piotroski F-Score, Altman Z-Score and Beneish M-Score, calculated from the annual
income statement, balance sheet and cash flow statement that yfinance exposes.

These replace the hardcoded profile table that used to live in deep_intelligence:
every symbol outside a five-name list received a constant quality score of 74,
which made the forensic quarter of the alpha score a no-op.

Statements are fetched at most once per REFRESH_AFTER_DAYS per symbol and cached
on disk, because the trading bot re-runs every five minutes and three statement
downloads per symbol would otherwise dominate every cycle.
"""
import datetime
import json
import os
import time
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import yfinance as yf

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "fundamentals_cache.json")
REFRESH_AFTER_DAYS = 7
# Upper bound on statement downloads per process, so one run can never stall the bot
MAX_REFRESHES_PER_RUN = 4

_refreshes_this_run = 0
_memory_cache: Dict[str, Dict[str, Any]] = {}


# ----------------------------------------------------------------------------
# Statement helpers
# ----------------------------------------------------------------------------
def _pick(df: Optional[pd.DataFrame], names, col: int) -> Optional[float]:
    """Reads a line item by any of its known labels for the given year column."""
    if df is None or df.empty or col >= len(df.columns):
        return None
    for name in names:
        if name in df.index:
            try:
                val = df.loc[name].iloc[col]
            except Exception:
                continue
            if val is not None and not pd.isna(val):
                return float(val)
    return None


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


# ----------------------------------------------------------------------------
# Piotroski F-Score (0-9)
# ----------------------------------------------------------------------------
def compute_piotroski(inc: pd.DataFrame, bal: pd.DataFrame,
                      cf: pd.DataFrame) -> Tuple[Optional[int], Dict[str, Any]]:
    """Nine binary tests across profitability, leverage and efficiency.

    Needs two comparable years; returns None when the filings do not provide them.
    """
    if any(d is None or d.empty or len(d.columns) < 2 for d in (inc, bal, cf)):
        return None, {"reason": "Weniger als zwei Geschäftsjahre verfügbar"}

    def year(i):
        return {
            "net_income": _pick(inc, ["Net Income", "Net Income Common Stockholders"], i),
            "revenue": _pick(inc, ["Total Revenue", "Operating Revenue"], i),
            "gross_profit": _pick(inc, ["Gross Profit"], i),
            "assets": _pick(bal, ["Total Assets"], i),
            "cur_assets": _pick(bal, ["Current Assets"], i),
            "cur_liab": _pick(bal, ["Current Liabilities"], i),
            "lt_debt": _pick(bal, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"], i),
            "shares": _pick(bal, ["Ordinary Shares Number", "Share Issued"], i),
            "cfo": _pick(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], i),
        }

    t0, t1 = year(0), year(1)
    checks: Dict[str, Optional[bool]] = {}

    roa0 = _safe_div(t0["net_income"], t0["assets"])
    roa1 = _safe_div(t1["net_income"], t1["assets"])
    cfo_ta0 = _safe_div(t0["cfo"], t0["assets"])

    # Profitability
    checks["ROA positiv"] = (roa0 > 0) if roa0 is not None else None
    checks["Operativer Cashflow positiv"] = (t0["cfo"] > 0) if t0["cfo"] is not None else None
    checks["ROA gestiegen"] = (roa0 > roa1) if (roa0 is not None and roa1 is not None) else None
    checks["Cashflow > Gewinn (keine Accruals)"] = (
        (cfo_ta0 > roa0) if (cfo_ta0 is not None and roa0 is not None) else None)

    # Leverage & liquidity
    lev0 = _safe_div(t0["lt_debt"] or 0.0, t0["assets"])
    lev1 = _safe_div(t1["lt_debt"] or 0.0, t1["assets"])
    checks["Verschuldung gesunken"] = (lev0 <= lev1) if (lev0 is not None and lev1 is not None) else None

    cr0 = _safe_div(t0["cur_assets"], t0["cur_liab"])
    cr1 = _safe_div(t1["cur_assets"], t1["cur_liab"])
    checks["Liquiditätsgrad gestiegen"] = (cr0 > cr1) if (cr0 is not None and cr1 is not None) else None

    checks["Keine Kapitalverwässerung"] = (
        (t0["shares"] <= t1["shares"] * 1.02)
        if (t0["shares"] is not None and t1["shares"] is not None) else None)

    # Efficiency
    gm0 = _safe_div(t0["gross_profit"], t0["revenue"])
    gm1 = _safe_div(t1["gross_profit"], t1["revenue"])
    checks["Bruttomarge gestiegen"] = (gm0 > gm1) if (gm0 is not None and gm1 is not None) else None

    at0 = _safe_div(t0["revenue"], t0["assets"])
    at1 = _safe_div(t1["revenue"], t1["assets"])
    checks["Kapitalumschlag gestiegen"] = (at0 > at1) if (at0 is not None and at1 is not None) else None

    decided = {k: v for k, v in checks.items() if v is not None}
    if len(decided) < 6:
        return None, {"reason": f"Nur {len(decided)} von 9 Kriterien berechenbar", "checks": checks}

    score = sum(1 for v in decided.values() if v)
    # Scale to the full 0-9 range when a criterion was not computable
    if len(decided) < 9:
        score = round(score * 9.0 / len(decided))
    return int(score), {"checks": checks, "decided": len(decided)}


# ----------------------------------------------------------------------------
# Altman Z-Score
# ----------------------------------------------------------------------------
# Altman calibrated the model on manufacturers. Banks and insurers carry leverage
# by design and score in the "distress" band while perfectly healthy, so the Z is
# reported as not applicable rather than as a false alarm.
NON_ALTMAN_SECTORS = {"financial services", "financials", "banks", "insurance", "real estate"}


def compute_altman_z(inc: pd.DataFrame, bal: pd.DataFrame,
                     market_cap: Optional[float],
                     sector: Optional[str] = None) -> Tuple[Optional[float], Dict[str, Any]]:
    """Z = 1.2·X1 + 1.4·X2 + 3.3·X3 + 0.6·X4 + 1.0·X5 (public industrials)."""
    if sector and sector.strip().lower() in NON_ALTMAN_SECTORS:
        return None, {"reason": f"Nicht anwendbar auf Sektor '{sector}' (Finanzwerte)",
                      "not_applicable": True}
    if bal is None or bal.empty:
        return None, {"reason": "Keine Bilanz verfügbar"}

    assets = _pick(bal, ["Total Assets"], 0)
    if not assets:
        return None, {"reason": "Bilanzsumme fehlt"}

    cur_assets = _pick(bal, ["Current Assets"], 0)
    cur_liab = _pick(bal, ["Current Liabilities"], 0)
    retained = _pick(bal, ["Retained Earnings"], 0)
    equity = _pick(bal, ["Stockholders Equity", "Common Stock Equity"], 0)
    ebit = _pick(inc, ["EBIT", "Operating Income", "Total Operating Income As Reported"], 0)
    revenue = _pick(inc, ["Total Revenue", "Operating Revenue"], 0)

    total_liab = _pick(bal, ["Total Liabilities Net Minority Interest"], 0)
    if total_liab is None and equity is not None:
        total_liab = assets - equity

    x1 = _safe_div((cur_assets - cur_liab) if (cur_assets is not None and cur_liab is not None) else None, assets)
    x2 = _safe_div(retained, assets)
    x3 = _safe_div(ebit, assets)
    x4 = _safe_div(market_cap, total_liab)
    x5 = _safe_div(revenue, assets)

    parts = {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5}
    if sum(1 for v in parts.values() if v is None) > 1:
        return None, {"reason": "Zu viele Bilanzpositionen fehlen", "parts": parts}

    z = (1.2 * (x1 or 0) + 1.4 * (x2 or 0) + 3.3 * (x3 or 0)
         + 0.6 * (x4 or 0) + 1.0 * (x5 or 0))
    return round(z, 2), {"parts": {k: (round(v, 3) if v is not None else None) for k, v in parts.items()}}


# ----------------------------------------------------------------------------
# Beneish M-Score
# ----------------------------------------------------------------------------
def compute_beneish_m(inc: pd.DataFrame, bal: pd.DataFrame,
                      cf: pd.DataFrame) -> Tuple[Optional[float], Dict[str, Any]]:
    """Eight-variable earnings-manipulation model. Above -1.78 is a red flag."""
    if any(d is None or d.empty or len(d.columns) < 2 for d in (inc, bal, cf)):
        return None, {"reason": "Weniger als zwei Geschäftsjahre verfügbar"}

    def year(i):
        return {
            "receivables": _pick(bal, ["Accounts Receivable", "Receivables"], i),
            "revenue": _pick(inc, ["Total Revenue", "Operating Revenue"], i),
            "cogs": _pick(inc, ["Cost Of Revenue", "Reconciled Cost Of Revenue"], i),
            "cur_assets": _pick(bal, ["Current Assets"], i),
            "ppe": _pick(bal, ["Net PPE"], i),
            "securities": _pick(bal, ["Available For Sale Securities", "Other Short Term Investments"], i) or 0.0,
            "assets": _pick(bal, ["Total Assets"], i),
            "depreciation": _pick(cf, ["Depreciation And Amortization", "Depreciation Amortization Depletion"], i),
            "sga": _pick(inc, ["Selling General And Administration"], i),
            "cur_liab": _pick(bal, ["Current Liabilities"], i),
            "lt_debt": _pick(bal, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"], i) or 0.0,
            "net_income": _pick(inc, ["Net Income Continuous Operations", "Net Income"], i),
            "cfo": _pick(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], i),
        }

    t, p = year(0), year(1)
    try:
        dsri = _safe_div(_safe_div(t["receivables"], t["revenue"]), _safe_div(p["receivables"], p["revenue"]))
        gmi = _safe_div(
            _safe_div((p["revenue"] - p["cogs"]) if None not in (p["revenue"], p["cogs"]) else None, p["revenue"]),
            _safe_div((t["revenue"] - t["cogs"]) if None not in (t["revenue"], t["cogs"]) else None, t["revenue"]))

        def soft_assets(y):
            if None in (y["assets"], y["cur_assets"], y["ppe"]):
                return None
            return 1.0 - (y["cur_assets"] + y["ppe"] + y["securities"]) / y["assets"]

        aqi = _safe_div(soft_assets(t), soft_assets(p))
        sgi = _safe_div(t["revenue"], p["revenue"])
        depi = _safe_div(
            _safe_div(p["depreciation"], (p["depreciation"] + p["ppe"]) if None not in (p["depreciation"], p["ppe"]) else None),
            _safe_div(t["depreciation"], (t["depreciation"] + t["ppe"]) if None not in (t["depreciation"], t["ppe"]) else None))
        sgai = _safe_div(_safe_div(t["sga"], t["revenue"]), _safe_div(p["sga"], p["revenue"]))
        lvgi = _safe_div(
            _safe_div((t["cur_liab"] + t["lt_debt"]) if t["cur_liab"] is not None else None, t["assets"]),
            _safe_div((p["cur_liab"] + p["lt_debt"]) if p["cur_liab"] is not None else None, p["assets"]))
        tata = _safe_div((t["net_income"] - t["cfo"]) if None not in (t["net_income"], t["cfo"]) else None, t["assets"])
    except Exception as exc:
        return None, {"reason": f"Berechnung fehlgeschlagen: {exc}"}

    vals = {"DSRI": dsri, "GMI": gmi, "AQI": aqi, "SGI": sgi,
            "DEPI": depi, "SGAI": sgai, "LVGI": lvgi, "TATA": tata}
    if sum(1 for v in vals.values() if v is None) > 2:
        return None, {"reason": "Zu viele Kennzahlen fehlen", "parts": vals}

    # Missing ratios default to 1.0 (neutral), TATA to 0.0
    g = lambda k, d=1.0: vals[k] if vals[k] is not None else d
    m = (-4.84 + 0.920 * g("DSRI") + 0.528 * g("GMI") + 0.404 * g("AQI")
         + 0.892 * g("SGI") + 0.115 * g("DEPI") - 0.172 * g("SGAI")
         + 4.679 * g("TATA", 0.0) - 0.327 * g("LVGI"))
    return round(m, 2), {"parts": {k: (round(v, 3) if v is not None else None) for k, v in vals.items()}}


# ----------------------------------------------------------------------------
# Cache + public entry point
# ----------------------------------------------------------------------------
_SCAN_SECTORS: Optional[Dict[str, str]] = None


def _sector_from_scan(symbol: str) -> Optional[str]:
    """Sector from the latest market scan.

    yfinance's .info returns 404 for many European listings, so Munich Re came
    back without a sector and was scored with Altman anyway - landing in the
    distress zone purely because insurers carry leverage by design.
    """
    global _SCAN_SECTORS
    if _SCAN_SECTORS is None:
        _SCAN_SECTORS = {}
        try:
            path = os.path.join(os.path.dirname(__file__), "..", "data", "market_scan_results.json")
            with open(path, "r", encoding="utf-8") as fh:
                for row in json.load(fh).get("data", []):
                    if row.get("symbol") and row.get("sector"):
                        _SCAN_SECTORS[row["symbol"]] = row["sector"]
        except Exception:
            pass
    return _SCAN_SECTORS.get(symbol)


def _load_cache() -> Dict[str, Any]:
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=1, ensure_ascii=False)
    except Exception:
        pass


def _is_fresh(entry: Dict[str, Any]) -> bool:
    try:
        age = time.time() - float(entry.get("fetched_ts", 0))
        return age < REFRESH_AFTER_DAYS * 86400
    except Exception:
        return False


def get_fundamental_scores(symbol: str) -> Dict[str, Any]:
    """Piotroski / Altman / Beneish for one symbol, disk-cached for a week.

    Always returns a dict carrying `available`. When the filings cannot be read
    (crypto, futures, many small caps) the caller is told so explicitly instead
    of receiving a constant that looks like a measurement.
    """
    global _refreshes_this_run

    if symbol in _memory_cache:
        return _memory_cache[symbol]

    cache = _load_cache()
    entry = cache.get(symbol)
    if entry and _is_fresh(entry):
        _memory_cache[symbol] = entry["scores"]
        return entry["scores"]

    # Instruments that simply have no filings
    if "-USD" in symbol or "=" in symbol:
        scores = {"available": False, "reason": "Kein bilanzierendes Unternehmen (Krypto/Future)"}
        cache[symbol] = {"fetched_ts": time.time(), "scores": scores}
        _save_cache(cache)
        _memory_cache[symbol] = scores
        return scores

    if _refreshes_this_run >= MAX_REFRESHES_PER_RUN:
        # Budget spent: prefer a stale cached value over a fabricated one
        if entry:
            _memory_cache[symbol] = entry["scores"]
            return entry["scores"]
        return {"available": False, "reason": "Noch nicht abgerufen (Budget dieses Laufs erschöpft)"}

    _refreshes_this_run += 1
    try:
        t = yf.Ticker(symbol)
        inc, bal, cf = t.income_stmt, t.balance_sheet, t.cashflow
        market_cap = None
        try:
            market_cap = float(t.fast_info.market_cap)
        except Exception:
            market_cap = None
        sector = None
        try:
            sector = (t.info or {}).get("sector")
        except Exception:
            sector = None
        if not sector:
            sector = _sector_from_scan(symbol)

        piotroski, p_det = compute_piotroski(inc, bal, cf)
        altman, a_det = compute_altman_z(inc, bal, market_cap, sector)
        beneish, b_det = compute_beneish_m(inc, bal, cf)
    except Exception as exc:
        scores = {"available": False, "reason": f"Abruf fehlgeschlagen: {type(exc).__name__}"}
        _memory_cache[symbol] = scores
        return scores

    if piotroski is None and altman is None:
        scores = {"available": False,
                  "reason": p_det.get("reason") or a_det.get("reason") or "Keine Jahresabschlüsse"}
    else:
        scores = {
            "available": True,
            "piotroski": piotroski,
            "piotroski_detail": p_det.get("checks"),
            "altman_z": altman,
            "altman_detail": a_det.get("parts"),
            "altman_not_applicable": bool(a_det.get("not_applicable")),
            "sector": sector,
            "beneish_m": beneish,
            "beneish_detail": b_det.get("parts"),
            "computed_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        }

    cache[symbol] = {"fetched_ts": time.time(), "scores": scores}
    _save_cache(cache)
    _memory_cache[symbol] = scores
    return scores
