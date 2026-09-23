"""What happened at the exit - and what happened after it.

The retrospective judged the system on entry quality and on aggregate outcome
statistics. Both are blind to the failure mode that cost the short-term depot
the most money: an exit that is technically not a loss.

Seven of fourteen closed short-term trades ended between -2.5% and +2%. In the
win rate they look like small losses, in the expectancy they barely register,
and the average-loss figure actually *improves* when they are added. Nothing in
the data the retrospective received could show that five of those seven
positions then ran 3-17% higher without their owner. A near-zero exit and a
well-timed escape are indistinguishable until you look at the price after the
sale.

This module supplies exactly those two missing views:

  1. Closed trades grouped by exit mechanism - stop, breakeven stop, trailing
     stop, thesis break, end-of-day liquidation - each with its count, its share
     and its average result. A mechanism that fires often and earns nothing is
     visible here and nowhere else.
  2. What the price did after the exit, per mechanism. This is the part that
     separates "the stop saved us" from "the stop threw us out": the same -0.5%
     exit is a success if the stock fell another 8% and an error if it rose 16%.

Point 2 needs market data and is therefore optional - if the download fails the
grouping still stands on its own.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.paths import data_file

DB_FILE = data_file("portfolio.db")

#: How far the follow-up looks past the exit. Long enough for a swing move to
#: play out, short enough that it is still attributable to the exit decision.
FOLLOW_UP_DAYS = 21

#: Exits within this band of the entry price are the ones worth separating out:
#: neither a real loss nor a win, they are the trades the system let go of.
NEAR_ZERO_BAND_PCT = 2.5


def classify_exit(reason: str, pnl_pct: Optional[float]) -> str:
    """Name the mechanism that ended the trade.

    Matched on the reason text the selling code writes. Breakeven stops carry
    their own marker since the trigger was raised to 2 ATR; older rows are
    recovered from the loss being far too small for a protective stop.
    """
    r = (reason or "").lower()
    if "knock-out" in r or "knock out" in r:
        return "Knock-Out (Totalverlust)"
    if "breakeven" in r:
        return "Breakeven-Stop"
    if "trailing" in r:
        return "Trailing-Stop (Gewinn gesichert)"
    if "eod" in r or "pflichtverkauf" in r or "uebernacht" in r or "übernacht" in r:
        return "EOD-Zwangsverkauf"
    if "thesen" in r or "these" in r:
        return "Thesen-Ausstieg"
    if "derisking" in r:
        return "Freitags-Derisking"
    if "stop-loss" in r or "stop loss" in r:
        # Before breakeven stops were labelled they hid in here: a stop that
        # exits within a hair of the entry price cannot be the protective stop,
        # which sits several percent away by construction.
        if pnl_pct is not None and -NEAR_ZERO_BAND_PCT <= pnl_pct <= 0:
            return "Breakeven-Stop"
        return "Stop-Loss"
    if "take-profit" in r or "ziel" in r or "gewinnmitnahme" in r:
        return "Take-Profit"
    if "swap" in r or "tausch" in r or "umschicht" in r:
        return "Umschichtung"
    return "Sonstiges"


def _is_market_ticker(symbol: str) -> bool:
    """True for symbols yfinance can price - i.e. not a certificate WKN.

    Derivatives are carried under their WKN (KO962646), which no market data
    feed serves. Their follow-up would be meaningless anyway: the certificate is
    the wrapper, not the asset.
    """
    s = (symbol or "").strip().upper()
    if not s or len(s) > 12:
        return False
    if re.fullmatch(r"[A-Z]{2}[0-9A-Z]{4,10}", s) and any(c.isdigit() for c in s):
        return False                      # WKN / ISIN shape
    return bool(re.fullmatch(r"[A-Z0-9]{1,6}([.\-][A-Z]{2,4})?", s))


def _closed_trades(depot_id: str, days: int) -> List[Dict[str, Any]]:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT symbol, sell_price, pnl, pnl_pct, reason, executed_at FROM trades "
            "WHERE depot_id = ? AND trade_type = 'SELL' AND pnl IS NOT NULL "
            "AND substr(executed_at, 1, 10) >= ? ORDER BY executed_at",
            (depot_id, since)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _follow_up(trades: List[Dict[str, Any]]) -> Dict[int, Dict[str, float]]:
    """Price development after each exit, keyed by index into `trades`.

    One batched download over the whole span, then sliced per trade - a request
    per trade would make the nightly run depend on dozens of round trips.
    """
    import pandas as pd
    import yfinance as yf

    candidates = [(i, t) for i, t in enumerate(trades)
                  if _is_market_ticker(t.get("symbol", "")) and t.get("sell_price")]
    if not candidates:
        return {}

    symbols = sorted({t["symbol"] for _, t in candidates})
    start = min(str(t["executed_at"])[:10] for _, t in candidates)
    data = yf.download(symbols, start=start,
                       end=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                       progress=False, auto_adjust=True, threads=True)
    if data is None or data.empty:
        return {}

    out: Dict[int, Dict[str, float]] = {}
    for i, t in candidates:
        try:
            closes = data["Close"][t["symbol"]] if len(symbols) > 1 else data["Close"]
            closes = closes.dropna()
            if closes.empty:
                continue
            exit_day = pd.Timestamp(str(t["executed_at"])[:10])
            window = closes[(closes.index > exit_day) &
                            (closes.index <= exit_day + pd.Timedelta(days=FOLLOW_UP_DAYS))]
            if window.empty:
                continue
            ref = float(t["sell_price"])
            if ref <= 0:
                continue
            out[i] = {
                "days_observed": int(len(window)),
                "change_pct": round((float(window.iloc[-1]) / ref - 1.0) * 100.0, 2),
                "best_pct": round((float(window.max()) / ref - 1.0) * 100.0, 2),
                "worst_pct": round((float(window.min()) / ref - 1.0) * 100.0, 2),
            }
        except Exception:
            continue
    return out


def analyse_exits(depot_id: str, days: int = 90,
                  with_follow_up: bool = True) -> Dict[str, Any]:
    """Closed trades grouped by exit mechanism, with post-exit development."""
    trades = _closed_trades(depot_id, days)
    if not trades:
        return {"available": False,
                "reason": f"Keine abgeschlossenen Trades in {days} Tagen."}

    follow: Dict[int, Dict[str, float]] = {}
    follow_error: Optional[str] = None
    if with_follow_up:
        try:
            follow = _follow_up(trades)
        except Exception as e:            # market data must never break the run
            follow, follow_error = {}, str(e)[:120]

    groups: Dict[str, Dict[str, Any]] = {}
    for i, t in enumerate(trades):
        cat = classify_exit(t.get("reason", ""), t.get("pnl_pct"))
        g = groups.setdefault(cat, {"count": 0, "pnl_sum": 0.0, "pnl_pcts": [],
                                    "after": [], "best_after": []})
        g["count"] += 1
        g["pnl_sum"] += float(t.get("pnl") or 0.0)
        if t.get("pnl_pct") is not None:
            g["pnl_pcts"].append(float(t["pnl_pct"]))
        if i in follow:
            g["after"].append(follow[i]["change_pct"])
            g["best_after"].append(follow[i]["best_pct"])

    total = len(trades)
    rows = []
    for cat, g in groups.items():
        row: Dict[str, Any] = {
            "ausstiegsgrund": cat,
            "anzahl": g["count"],
            "anteil_pct": round(g["count"] / total * 100.0, 1),
            "pnl_summe_eur": round(g["pnl_sum"], 2),
            "pnl_schnitt_eur": round(g["pnl_sum"] / g["count"], 2),
            "pnl_schnitt_pct": (round(sum(g["pnl_pcts"]) / len(g["pnl_pcts"]), 2)
                                if g["pnl_pcts"] else None),
        }
        if g["after"]:
            n = len(g["after"])
            # The decisive number: what the position did AFTER we sold it.
            # Positive means the exit cost money that the trade had earned.
            row["kurs_nach_ausstieg_schnitt_pct"] = round(sum(g["after"]) / n, 2)
            row["kurs_nach_ausstieg_bestfall_pct"] = round(sum(g["best_after"]) / n, 2)
            row["davon_weiter_gestiegen"] = sum(1 for a in g["after"] if a > 0)
            row["nachbeobachtet"] = n
        rows.append(row)

    rows.sort(key=lambda r: r["anzahl"], reverse=True)

    near_zero = [t for t in trades
                 if t.get("pnl_pct") is not None
                 and -NEAR_ZERO_BAND_PCT <= float(t["pnl_pct"]) <= 2.0]
    result: Dict[str, Any] = {
        "available": True,
        "zeitraum_tage": days,
        "abgeschlossene_trades": total,
        "nachbeobachtungsfenster_tage": FOLLOW_UP_DAYS,
        "gruppen": rows,
        "nullsummen_ausstiege": {
            "anzahl": len(near_zero),
            "anteil_pct": round(len(near_zero) / total * 100.0, 1),
            "definition": f"Ergebnis zwischen -{NEAR_ZERO_BAND_PCT}% und +2.0%",
        },
    }
    if follow_error:
        result["nachbeobachtung"] = f"nicht verfuegbar ({follow_error})"
    elif not follow:
        result["nachbeobachtung"] = "nicht verfuegbar (keine marktgehandelten Symbole)"
    return result


def format_for_prompt(depot_id: str, days: int = 90) -> str:
    """Readable block for the retrospective prompt."""
    import json
    try:
        a = analyse_exits(depot_id, days)
    except Exception as e:
        return f"Ausstiegsanalyse nicht verfuegbar: {e}"
    if not a.get("available"):
        return a.get("reason", "Keine Daten.")
    return json.dumps(a, indent=2, ensure_ascii=False)
