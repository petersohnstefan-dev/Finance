"""Entwickelt sich das Depot - und nicht nur: wo steht es?

The retrospective saw two numbers: today, and everything since inception. All
time is dominated by the worst period the system ever had, including a 1570 EUR
loss from a certificate defect, so the verdict was "catastrophic" every single
night no matter what changed in between. A system that is told it is failing
every evening keeps prescribing aggressive corrections, which is how the
parameter drift of 14.-16.09. started.

The obvious fix - hand it a rolling window - has a trap of its own. Measured as
a mean, the daytrader looks like this:

    Tag 8-14        -171.96 EUR je Trade
    letzte 7 Tage    -50.85 EUR je Trade

which reads as a threefold improvement and is almost entirely the defect loss
dropping out of the window. Excluding that single trade the same comparison is
-55.45 against -50.85: flat. The median moves from -45.27 to -29.64, so there
IS an improvement, but a third of the apparent size.

Every window is therefore reported three ways - mean, median, and mean with
trades already recorded as defect-caused removed. The median is the one to read
a trend from; a mean that moves because of one trade is not a trend.
"""
from __future__ import annotations

import json
import sqlite3
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.paths import data_file

DB_FILE = data_file("portfolio.db")
STATE_FILE = data_file("portfolios.json")

#: Windows the trend is reported over, as (label, from_days_ago, to_days_ago).
#: "to" is exclusive and counted backwards, so (7, 0) is the last seven days.
WINDOWS = [
    ("letzte 7 Tage", 7, 0),
    ("Tag 8-14", 14, 7),
    ("Tag 15-28", 28, 14),
    ("seit Depotstart", 100000, 0),
]

#: Below this many closed trades a window carries no trend information at all.
MIN_TRADES_FOR_TREND = 5


def _defect_trades(depot_id: str) -> List[Dict[str, Any]]:
    """Losses already recorded as technical defects rather than strategy.

    Read from the daily-limit waivers, which is where such a loss is documented
    when it is excluded from the daily stop. Using that list rather than a fresh
    judgement keeps one decision in one place.
    """
    try:
        with open(STATE_FILE, encoding="utf-8") as fh:
            state = json.load(fh)
        return list((state.get("daily_limit_waivers") or {}).get(depot_id) or [])
    except Exception:
        return []


def _is_defect(trade: Dict[str, Any], waivers: List[Dict[str, Any]]) -> bool:
    """True when this closed trade is one of the recorded defect losses."""
    tag = str(trade.get("date") or "")[:10]
    pnl = float(trade.get("pnl") or 0.0)
    for w in waivers:
        if str(w.get("date"))[:10] != tag:
            continue
        betrag = float(w.get("amount") or 0.0)
        if betrag > 0 and abs(abs(pnl) - betrag) <= max(1.0, betrag * 0.01):
            return True
    return False


def _closed_trades(depot_id: str) -> List[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(DB_FILE)
        rows = conn.execute(
            "SELECT substr(executed_at, 1, 10), pnl, pnl_pct FROM trades "
            "WHERE depot_id = ? AND trade_type = 'SELL' AND pnl IS NOT NULL "
            "ORDER BY executed_at", (depot_id,)).fetchall()
        conn.close()
        return [{"date": r[0], "pnl": float(r[1]),
                 "pnl_pct": (float(r[2]) if r[2] is not None else None)} for r in rows]
    except Exception:
        return []


def _stats(trades: List[Dict[str, Any]], waivers: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(trades)
    if n == 0:
        return {"trades": 0}
    pnls = [t["pnl"] for t in trades]
    gewinner = [p for p in pnls if p > 0]
    bereinigt = [t["pnl"] for t in trades if not _is_defect(t, waivers)]
    out: Dict[str, Any] = {
        "trades": n,
        "trefferquote_pct": round(len(gewinner) / n * 100.0, 1),
        "summe_eur": round(sum(pnls), 2),
        "mittel_eur": round(sum(pnls) / n, 2),
        "median_eur": round(statistics.median(pnls), 2),
    }
    if len(bereinigt) != n and bereinigt:
        out["defekte_ausgeschlossen"] = n - len(bereinigt)
        out["mittel_ohne_defekte_eur"] = round(sum(bereinigt) / len(bereinigt), 2)
    if n < MIN_TRADES_FOR_TREND:
        out["hinweis"] = (f"nur {n} Trades - aus diesem Fenster laesst sich kein "
                          f"Trend ablesen")
    return out


def analyse_trend(depot_id: str) -> Dict[str, Any]:
    """Rolling windows with mean, median and a defect-adjusted mean."""
    trades = _closed_trades(depot_id)
    if not trades:
        return {"available": False, "reason": "Keine abgeschlossenen Trades."}
    waivers = _defect_trades(depot_id)
    heute = datetime.now().date()

    fenster: Dict[str, Any] = {}
    for label, von, bis in WINDOWS:
        a = (heute - timedelta(days=von)).isoformat()
        b = (heute - timedelta(days=bis)).isoformat() if bis else "9999-99-99"
        fenster[label] = _stats([t for t in trades if a <= t["date"] < b], waivers)

    ergebnis: Dict[str, Any] = {
        "available": True,
        "fenster": fenster,
        "lesehilfe": ("Trend am Median und am defektbereinigten Mittel ablesen. Ein "
                      "Mittelwert, der sich wegen eines einzigen Trades bewegt, ist "
                      "kein Trend."),
    }

    # Explicit comparison of the two most recent full windows, with the caveat
    # attached rather than left to be inferred.
    jung, alt = fenster["letzte 7 Tage"], fenster["Tag 8-14"]
    if jung.get("trades", 0) >= MIN_TRADES_FOR_TREND and \
            alt.get("trades", 0) >= MIN_TRADES_FOR_TREND:
        d_median = jung["median_eur"] - alt["median_eur"]
        d_quote = jung["trefferquote_pct"] - alt["trefferquote_pct"]
        basis_jung = jung.get("mittel_ohne_defekte_eur", jung["mittel_eur"])
        basis_alt = alt.get("mittel_ohne_defekte_eur", alt["mittel_eur"])
        ergebnis["vergleich_7d_gegen_8_14d"] = {
            "median_differenz_eur": round(d_median, 2),
            "trefferquote_differenz_pp": round(d_quote, 1),
            "mittel_bereinigt_differenz_eur": round(basis_jung - basis_alt, 2),
            "richtung": ("besser" if d_median > 0 else
                         "schlechter" if d_median < 0 else "unveraendert"),
        }
    else:
        ergebnis["vergleich_7d_gegen_8_14d"] = (
            "nicht aussagekraeftig - mindestens "
            f"{MIN_TRADES_FOR_TREND} Trades je Fenster noetig")
    return ergebnis


def format_for_prompt(depot_id: str) -> str:
    try:
        a = analyse_trend(depot_id)
    except Exception as e:
        return f"Trendanalyse nicht verfuegbar: {e}"
    if not a.get("available"):
        return a.get("reason", "Keine Daten.")
    return json.dumps(a, indent=2, ensure_ascii=False)
