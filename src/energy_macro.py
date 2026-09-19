"""Real energy and macro data: crack spread, EIA inventories, FRED inflation.

Replaces fixed strings that never moved. The dashboard claimed a crack spread of
"$22.50 / Barrel (Solide Raffinerie-Margen)" while the computed value was 62 USD -
historically extreme, and precisely the shortage signal the display was hiding.
EIA inventories ("-3.4 Mio. Barrel"), OPEC spare capacity and the entire
FREDMacroEngine were fixed strings too.

Crack spread needs no credentials. EIA and FRED each need a free API key
(EIA_API_KEY, FRED_API_KEY). Without them the functions report available=False
with a reason - they never invent a number, because an invented macro reading is
worse than none: it looks like a measurement and silently anchors every decision
built on top of it.

    EIA key:  https://www.eia.gov/opendata/   (free, no card)
    FRED key: https://fred.stlouisfed.org/docs/api/api_key.html  (free, instant)
"""
import datetime
import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
import yfinance as yf

from src.paths import data_file

CACHE_FILE = data_file("energy_macro_cache.json")

#: Inventories publish weekly (Wed 10:30 ET), CPI monthly - no need to refetch often.
EIA_TTL = 6 * 3600
FRED_TTL = 12 * 3600
CRACK_TTL = 900

_memory: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------- cache
def _cache_get(key: str, ttl: float) -> Optional[Any]:
    entry = _memory.get(key)
    if entry and (time.time() - entry["ts"]) < ttl:
        return entry["data"]
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as fh:
            disk = json.load(fh)
        entry = disk.get(key)
        if entry and (time.time() - entry["ts"]) < ttl:
            _memory[key] = entry
            return entry["data"]
    except Exception:
        pass
    return None


def _cache_put(key: str, data: Any) -> None:
    entry = {"ts": time.time(), "data": data}
    _memory[key] = entry
    try:
        disk = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as fh:
                disk = json.load(fh)
        disk[key] = entry
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump(disk, fh, indent=1, ensure_ascii=False)
    except Exception:
        pass


def _stale(key: str) -> Optional[Any]:
    """Last known value regardless of age - better than nothing when a fetch fails."""
    entry = _memory.get(key)
    if entry:
        return entry["data"]
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as fh:
            return (json.load(fh).get(key) or {}).get("data")
    except Exception:
        return None


# ------------------------------------------------------- crack spread
def get_crack_spread() -> Dict[str, Any]:
    """3:2:1 crack spread in USD/barrel, computed from futures.

    (2 x gasoline + 1 x heating oil - 3 x crude) / 3, with the products converted
    from USD/gallon to USD/barrel at 42 gallons. This is the refining margin, and
    it widens when products are scarce relative to crude - the clearest market read
    on a supply squeeze working its way downstream.
    """
    cached = _cache_get("crack", CRACK_TTL)
    if cached:
        return cached

    prices: Dict[str, Optional[float]] = {}
    for sym in ("CL=F", "RB=F", "HO=F"):
        try:
            hist = yf.Ticker(sym).history(period="5d")
            prices[sym] = float(hist["Close"].iloc[-1]) if not hist.empty else None
        except Exception:
            prices[sym] = None

    if not all(prices.values()):
        return {"available": False,
                "reason": "Futures-Kurse (CL=F/RB=F/HO=F) nicht abrufbar"}

    crude, gas, heat = prices["CL=F"], prices["RB=F"], prices["HO=F"]
    crack = (2 * gas * 42 + heat * 42 - 3 * crude) / 3

    # Historical context: 10-25 is a normal band, sustained highs mean product
    # shortage, lows mean refiners have no incentive to run crude.
    if crack >= 40:
        regime = "\U0001f6a8 Extrem hohe Raffineriemargen – Produktknappheit"
    elif crack >= 25:
        regime = "⚠️ Erhöhte Margen – angespannte Produktversorgung"
    elif crack >= 10:
        regime = "⚖️ Normale Raffineriemargen"
    else:
        regime = "\U0001f4c9 Schwache Margen – geringer Anreiz zu raffinieren"

    data = {
        "available": True,
        "crack_spread_usd": round(crack, 2),
        "crude_usd": round(crude, 2),
        "gasoline_usd_gal": round(gas, 4),
        "heating_oil_usd_gal": round(heat, 4),
        "regime": regime,
        "computed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    _cache_put("crack", data)
    return data


# --------------------------------------------------------------- EIA
def get_eia_inventories() -> Dict[str, Any]:
    """US commercial crude stocks, latest weeks, from the EIA v2 API."""
    key = os.environ.get("EIA_API_KEY")
    if not key:
        return {"available": False,
                "reason": "Kein EIA_API_KEY gesetzt (kostenlos unter "
                          "https://www.eia.gov/opendata/)"}

    cached = _cache_get("eia", EIA_TTL)
    if cached:
        return cached

    url = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
    params = {
        "api_key": key,
        "frequency": "weekly",
        "data[0]": "value",
        # WCESTUS1 = commercial crude excluding SPR, thousand barrels
        "facets[series][]": "WCESTUS1",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": "12",
    }
    try:
        resp = requests.get(url, params=params, timeout=12)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")
        rows = resp.json().get("response", {}).get("data", [])
    except Exception as exc:
        stale = _stale("eia")
        if stale:
            stale = dict(stale)
            stale["stale"] = True
            stale["reason"] = f"Abruf fehlgeschlagen ({type(exc).__name__}), letzter bekannter Stand"
            return stale
        return {"available": False, "reason": f"EIA-Abruf fehlgeschlagen: {exc}"}

    points = []
    for r in rows:
        try:
            points.append({"period": r.get("period"), "value": float(r.get("value"))})
        except (TypeError, ValueError):
            continue
    if len(points) < 2:
        return {"available": False, "reason": "EIA lieferte zu wenige Datenpunkte"}

    latest, prev = points[0], points[1]
    change = latest["value"] - prev["value"]
    # Four-week trend says more than a single print, which is noisy
    trend_4w = (latest["value"] - points[min(4, len(points) - 1)]["value"])

    if trend_4w < -15000:
        regime = "\U0001f6a8 Deutlicher Lagerabbau über 4 Wochen – Angebot knapp"
    elif trend_4w < -5000:
        regime = "⚠️ Lagerbestände sinken"
    elif trend_4w > 15000:
        regime = "\U0001f4c9 Deutlicher Lageraufbau – Angebot reichlich"
    else:
        regime = "⚖️ Lagerbestände weitgehend stabil"

    data = {
        "available": True,
        "latest_period": latest["period"],
        "stocks_mbbl": round(latest["value"] / 1000.0, 1),
        "change_week_mbbl": round(change / 1000.0, 1),
        "change_4w_mbbl": round(trend_4w / 1000.0, 1),
        "regime": regime,
        "history": [{"period": p["period"], "mbbl": round(p["value"] / 1000.0, 1)}
                    for p in points[:12]],
    }
    _cache_put("eia", data)
    return data


# -------------------------------------------------------------- FRED
FRED_SERIES = {
    "cpi_yoy": ("CPIAUCSL", "US-Verbraucherpreise (CPI)"),
    "core_cpi_yoy": ("CPILFESL", "US-Kerninflation"),
    "us_10y": ("DGS10", "US 10-Jahres-Rendite"),
    "us_2y": ("DGS2", "US 2-Jahres-Rendite"),
    "real_10y": ("DFII10", "US 10J-Realzins (TIPS)"),
}


def _fred_series(series_id: str, key: str, limit: int = 14) -> List[Dict[str, Any]]:
    resp = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={"series_id": series_id, "api_key": key, "file_type": "json",
                "sort_order": "desc", "limit": limit},
        timeout=12)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")
    out = []
    for o in resp.json().get("observations", []):
        try:
            out.append({"date": o["date"], "value": float(o["value"])})
        except (KeyError, TypeError, ValueError):
            continue   # FRED marks missing observations with "."
    return out


def get_fred_macro() -> Dict[str, Any]:
    """Inflation and yields from FRED. Replaces the fixed-string FREDMacroEngine."""
    key = os.environ.get("FRED_API_KEY")
    if not key:
        return {"available": False,
                "reason": "Kein FRED_API_KEY gesetzt (kostenlos unter "
                          "https://fred.stlouisfed.org/docs/api/api_key.html)"}

    cached = _cache_get("fred", FRED_TTL)
    if cached:
        return cached

    out: Dict[str, Any] = {"available": True,
                           "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    try:
        for name, (sid, label) in FRED_SERIES.items():
            obs = _fred_series(sid, key)
            if not obs:
                out[name] = None
                continue
            if name.endswith("_yoy"):
                # CPI is an index: year-over-year needs the reading 12 months back
                obs13 = _fred_series(sid, key, limit=14)
                if len(obs13) >= 13 and obs13[12]["value"]:
                    yoy = (obs13[0]["value"] / obs13[12]["value"] - 1.0) * 100.0
                    out[name] = round(yoy, 2)
                    out[name + "_asof"] = obs13[0]["date"]
                else:
                    out[name] = None
            else:
                out[name] = round(obs[0]["value"], 2)
                out[name + "_asof"] = obs[0]["date"]
            out[name + "_label"] = label
    except Exception as exc:
        stale = _stale("fred")
        if stale:
            stale = dict(stale)
            stale["stale"] = True
            stale["reason"] = f"Abruf fehlgeschlagen ({type(exc).__name__}), letzter bekannter Stand"
            return stale
        return {"available": False, "reason": f"FRED-Abruf fehlgeschlagen: {exc}"}

    cpi = out.get("cpi_yoy")
    if cpi is not None:
        if cpi >= 4.0:
            out["inflation_regime"] = "\U0001f6a8 Hohe Inflation – Druck auf Realrenditen und Bewertungen"
        elif cpi >= 2.8:
            out["inflation_regime"] = "⚠️ Inflation über Zielband"
        elif cpi >= 1.5:
            out["inflation_regime"] = "⚖️ Inflation nahe Zielband"
        else:
            out["inflation_regime"] = "\U0001f4c9 Niedrige Inflation"

    if out.get("us_10y") is not None and out.get("us_2y") is not None:
        spread = out["us_10y"] - out["us_2y"]
        out["curve_spread"] = round(spread, 2)
        out["curve_regime"] = ("\U0001f6a8 Invertierte Zinskurve" if spread < 0
                               else "⚖️ Normale Zinskurve")

    _cache_put("fred", out)
    return out


# ---------------------------------------------------- net liquidity
#: Fed balance sheet minus the two balances that drain reserves. All three are
#: FRED series; WALCL is in millions, the other two in billions.
LIQUIDITY_SERIES = {
    "fed_assets": ("WALCL", 1e-3),        # millions -> billions
    "treasury_account": ("WTREGEN", 1.0),
    "reverse_repo": ("RRPONTSYD", 1.0),
}


def get_net_liquidity() -> Dict[str, Any]:
    """US net liquidity = Fed balance sheet - TGA - reverse repo.

    The dashboard asserted "$6.05 Billionen USD (Stabil)" as a fixed string, and
    the macro panel built a regime verdict on top of it. The three components are
    public FRED series, so the figure can simply be computed.
    """
    key = os.environ.get("FRED_API_KEY")
    if not key:
        return {"available": False,
                "reason": "Kein FRED_API_KEY gesetzt (kostenlos unter "
                          "https://fred.stlouisfed.org/docs/api/api_key.html)"}

    cached = _cache_get("liquidity", FRED_TTL)
    if cached:
        return cached

    parts: Dict[str, Any] = {}
    try:
        for name, (sid, factor) in LIQUIDITY_SERIES.items():
            obs = _fred_series(sid, key, limit=8)
            if not obs:
                return {"available": False, "reason": f"FRED-Serie {sid} ohne Werte"}
            parts[name] = {"value_bn": obs[0]["value"] * factor,
                           "date": obs[0]["date"],
                           # four weeks back where the series allows it
                           "prev_bn": (obs[min(4, len(obs) - 1)]["value"] * factor)}
    except Exception as exc:
        stale = _stale("liquidity")
        if stale:
            stale = dict(stale)
            stale["stale"] = True
            stale["reason"] = f"Abruf fehlgeschlagen ({type(exc).__name__}), letzter Stand"
            return stale
        return {"available": False, "reason": f"FRED-Abruf fehlgeschlagen: {exc}"}

    net = (parts["fed_assets"]["value_bn"] - parts["treasury_account"]["value_bn"]
           - parts["reverse_repo"]["value_bn"])
    net_prev = (parts["fed_assets"]["prev_bn"] - parts["treasury_account"]["prev_bn"]
                - parts["reverse_repo"]["prev_bn"])
    delta = net - net_prev

    if delta > 50:
        regime = "🟢 Expansiv – Liquiditaet fliesst in die Maerkte"
    elif delta < -50:
        regime = "🚨 Restriktiv – Liquiditaet wird abgezogen"
    else:
        regime = "⚖️ Neutral – Liquiditaet weitgehend unveraendert"

    data = {
        "available": True,
        "net_liquidity_bn": round(net, 1),
        "net_liquidity_trn": round(net / 1000.0, 2),
        "delta_4w_bn": round(delta, 1),
        "regime": regime,
        "components": {k: {"mrd_usd": round(v["value_bn"], 1), "stand": v["date"]}
                       for k, v in parts.items()},
        "as_of": parts["fed_assets"]["date"],
    }
    _cache_put("liquidity", data)
    return data


# ------------------------------------------------------------ summary
def get_energy_macro_overview() -> Dict[str, Any]:
    """Everything at once, for the dashboard and the chat context."""
    return {"crack": get_crack_spread(),
            "inventories": get_eia_inventories(),
            "fred": get_fred_macro()}


def summarize() -> str:
    """Compact text - used by the chat context and the tribunal evidence."""
    o = get_energy_macro_overview()
    lines = []

    c = o["crack"]
    if c.get("available"):
        lines.append(f"- Rohoel (WTI) {c['crude_usd']} USD, Crack-Spread 3:2:1 "
                     f"{c['crack_spread_usd']} USD/Barrel: {c['regime']}")
    else:
        lines.append(f"- Crack-Spread nicht verfuegbar: {c.get('reason')}")

    i = o["inventories"]
    if i.get("available"):
        lines.append(f"- US-Rohoellager {i['stocks_mbbl']} Mio. Barrel "
                     f"(Stand {i['latest_period']}), Woche {i['change_week_mbbl']:+.1f}, "
                     f"4 Wochen {i['change_4w_mbbl']:+.1f}: {i['regime']}")
    else:
        lines.append(f"- Lagerbestaende nicht verfuegbar: {i.get('reason')}")

    f = o["fred"]
    if f.get("available"):
        if f.get("cpi_yoy") is not None:
            lines.append(f"- US-Inflation {f['cpi_yoy']}% (Kern {f.get('core_cpi_yoy')}%, "
                         f"Stand {f.get('cpi_yoy_asof')}): {f.get('inflation_regime')}")
        if f.get("us_10y") is not None:
            lines.append(f"- US-Renditen 10J {f['us_10y']}%, 2J {f.get('us_2y')}%, "
                         f"Realzins {f.get('real_10y')}%: {f.get('curve_regime')}")
    else:
        lines.append(f"- Inflations-/Zinsdaten nicht verfuegbar: {f.get('reason')}")

    return "\n".join(lines)
