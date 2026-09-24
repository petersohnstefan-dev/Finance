import sqlite3
import json
import datetime
import os
import re
from typing import Dict, Any, List, Optional

from src import incidents
from src import exit_analysis

try:
    import google.generativeai as genai
except ImportError:
    pass

from src.paths import data_file

DB_FILE = data_file("portfolio.db")
ALERTS_FILE = data_file("realtime_alerts.json")
STRATEGY_FILE = data_file("strategy.json")
ENTRY_DIAG_FILE = data_file("entry_diagnostics.json")

#: A parameter moved in one direction may not be moved the same way again until
#: its effect could plausibly show up in the statistics. Measured in CLOSED TRADES,
#: not in days: three days is one trade in the short-term depot and a dozen in the
#: daytrader, and a time-based lock merely slows a drift instead of stopping it -
#: at one step every four days the stop multiplier would have been walked from 2.5
#: back down to its 1.5 floor within a fortnight.
PARAM_CHANGE_MIN_TRADES = 5
#: How far back to look for previous changes at all.
PARAM_CHANGE_LOOKBACK_DAYS = 30
from zoneinfo import ZoneInfo
BERLIN_TZ = ZoneInfo("Europe/Berlin")

def get_berlin_now() -> datetime.datetime:
    try:
        return datetime.datetime.now(BERLIN_TZ)
    except Exception:
        return datetime.datetime.utcnow() + datetime.timedelta(hours=2)

def _migrate_ai_journal_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(ai_journal)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if not columns:
        cursor.execute('''
            CREATE TABLE ai_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                depot_id TEXT NOT NULL,
                date TEXT NOT NULL,
                mode TEXT DEFAULT "daily",
                win_rate REAL,
                best_trade TEXT,
                worst_trade TEXT,
                reflection TEXT,
                lesson TEXT,
                missed_opportunities TEXT,
                param_updates TEXT,
                UNIQUE(depot_id, date, mode)
            )
        ''')
        conn.commit()
    conn.close()

# Run migration on import
_migrate_ai_journal_db()

# Safety bounds for each tunable parameter — the AI cannot go outside these ranges
PARAM_SAFETY_BOUNDS = {
    # Capped at 3x, not 15x: a stop can only hold if the underlying needs a bigger
    # move than sl_pct/leverage to jump it between two five-minute checks. At 7-10x
    # that threshold (1.4-2.0%) is the same size as the entry criterion itself, and
    # nine trades that blew through the stop produced 94% of the depot's loss. The
    # journal may lower the lever, never raise it past what the polling can protect.
    "daytrade_max_leverage":          {"min": 1.0,   "max": 3.0,   "step": 0.5},
    "daytrade_stop_loss_pct":         {"min": 0.05,  "max": 0.30,  "step": 0.01},
    "daytrade_max_risk_per_trade_pct":{"min": 0.005, "max": 0.03,  "step": 0.005},
    "daytrade_min_risk_reward_ratio": {"min": 1.5,   "max": 4.0,   "step": 0.5},
    "daytrade_max_daily_loss_pct":    {"min": 0.02,  "max": 0.10,  "step": 0.01},
    "daytrade_max_daily_trades":      {"min": 2,     "max": 10,    "step": 1},
    "daytrade_min_entry_score":       {"min": 40,    "max": 90,    "step": 5},
    "daytrade_max_correlated_positions":{"min": 1,  "max": 4,     "step": 1},
    "daytrade_trailing_breakeven_pct":{"min": 0.02,  "max": 0.08,  "step": 0.01},
    "daytrade_trailing_lock_pct":     {"min": 0.03,  "max": 0.15,  "step": 0.01},
    "daytrade_trailing_aggressive_pct":{"min": 0.05, "max": 0.25,  "step": 0.01},
    "daytrade_vix_defensive_threshold":{"min": 18.0, "max": 35.0,  "step": 1.0},
    "daytrade_vix_pause_threshold":   {"min": 25.0,  "max": 45.0,  "step": 1.0},
    "daytrade_max_candidates_scored": {"min": 3,     "max": 20,    "step": 1},
    # short_term_trailing_start_pct was removed: the fixed +8% ratchet it fed no
    # longer exists, so tuning it would have optimised into the void.
    "short_term_stop_loss_pct":       {"min": 0.05,  "max": 0.25,  "step": 0.01},
    "short_term_stop_atr_mult":       {"min": 1.5,   "max": 4.0,   "step": 0.25},
    "short_term_trail_atr_mult":      {"min": 1.5,   "max": 4.0,   "step": 0.25},
    # Floor raised from 0.5 to 1.5: at 1.0 ATR the stop was pulled to the entry
    # price on any ordinary day, and three of three positions stopped out that way
    # rose an average of 14% in the three weeks after the exit. Below 1.5 the
    # trigger stops protecting profit and starts harvesting noise, so the
    # retrospective may no longer go back there - see the prompt constraint.
    "short_term_breakeven_trigger_atr":{"min": 1.5,  "max": 3.0,   "step": 0.25},
    "short_term_stop_min_pct":        {"min": 0.03,  "max": 0.12,  "step": 0.01},
    "short_term_stop_max_pct":        {"min": 0.15,  "max": 0.40,  "step": 0.05},
    "short_term_max_risk_per_trade_pct":{"min": 0.005, "max": 0.03, "step": 0.005},
    "short_term_min_alpha_score":     {"min": 40,    "max": 85,    "step": 5},
    "short_term_min_spike_pct":       {"min": 0.5,   "max": 5.0,   "step": 0.25},
    "short_term_max_candidates_scored":{"min": 5,    "max": 25,    "step": 1},
    # The weekly retrospective covers medium_term and long_term, but had no tunable
    # parameter under either prefix - it wrote an analysis every week that could not
    # change anything. Entry thresholds and the swap bar are opened up; position
    # counts, cash floors and the loss ceiling stay closed, since those are structure
    # and safety rather than strategy.
    "medium_term_min_score":          {"min": 60,    "max": 90,    "step": 5},
    "medium_term_hedge_vix_threshold":{"min": 22.0,  "max": 40.0,  "step": 2.0},
    "medium_term_hedge_exit_vix":     {"min": 15.0,  "max": 30.0,  "step": 2.0},
    "long_term_min_score":            {"min": 60,    "max": 95,    "step": 5},
    "long_term_swap_min_advantage":   {"min": 10,    "max": 40,    "step": 5},
    "long_term_bonus_pct":            {"min": 8.0,   "max": 25.0,  "step": 2.0},
}


def trading_day(now: Optional[datetime.datetime] = None) -> datetime.datetime:
    """The trading day a nightly run is about, not the calendar day it ran on.

    The cron fires at 20:30 UTC, but GitHub's queue can delay it past midnight
    Berlin time - on 18.09. it ran at 22:43 UTC, i.e. 00:43 on the 19th. The
    Friday retrospective was then stored under Saturday's date, which also made
    the duplicate-run guard check the wrong day. Anything before 06:00 belongs to
    the day before.
    """
    now = now or get_berlin_now()
    return now - datetime.timedelta(days=1) if now.hour < 6 else now


def _escape_control_chars_in_strings(text: str) -> str:
    """Escape raw control characters that sit inside JSON string literals.

    Last resort for a model that put a literal newline or tab in a value. Walks
    the text tracking whether it is inside a string, so control characters
    between tokens - which are legal whitespace - stay untouched.
    """
    out = []
    in_string = False
    escaped = False
    for ch in text:
        if in_string:
            if escaped:
                out.append(ch)
                escaped = False
                continue
            if ch == "\\":
                out.append(ch)
                escaped = True
                continue
            if ch == '"':
                in_string = False
                out.append(ch)
                continue
            if ch == "\n":
                out.append("\\n")
                continue
            if ch == "\r":
                out.append("\\r")
                continue
            if ch == "\t":
                out.append("\\t")
                continue
            if ord(ch) < 0x20:
                out.append("\\u%04x" % ord(ch))
                continue
            out.append(ch)
            continue
        if ch == '"':
            in_string = True
        out.append(ch)
    return "".join(out)


def parse_model_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Read the model's answer, tolerating the ways an LLM bends JSON.

    A single strict json.loads is the wrong tool here. On 23.09. the daytrader
    retrospective was lost because the model put a real line break inside a
    string value - "Invalid control character at char 3944" - and the salvage
    path retried with the same strict parser, so it failed identically. The
    whole analysis was discarded over a newline.

    Python's strict mode exists to reject exactly that, but the JSON spec's
    intent here is not worth a lost retrospective: the content is prose meant
    for a human. Each stage below is strictly more permissive than the last.
    """
    attempts = [
        ("strict", lambda t: json.loads(t)),
        ("kontrollzeichen erlaubt", lambda t: json.loads(t, strict=False)),
        ("nur der JSON-Block", lambda t: json.loads(
            re.search(r"\{.*\}", t, re.DOTALL).group(0), strict=False)),
        ("Kontrollzeichen maskiert", lambda t: json.loads(
            _escape_control_chars_in_strings(
                re.search(r"\{.*\}", t, re.DOTALL).group(0)))),
        ("ohne Komma am Blockende", lambda t: json.loads(
            re.sub(r",(\s*[}\]])", r"\1",
                   _escape_control_chars_in_strings(
                       re.search(r"\{.*\}", t, re.DOTALL).group(0))))),
    ]
    for _label, fn in attempts:
        try:
            res = fn(raw_text)
            if isinstance(res, dict):
                return res
        except Exception:
            continue
    return None


class AIJournalEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _load_strategy(self) -> Dict[str, Any]:
        """Loads current strategy parameters from strategy.json."""
        try:
            with open(STRATEGY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _save_strategy(self, params: Dict[str, Any]):
        """Writes updated strategy parameters to strategy.json."""
        with open(STRATEGY_FILE, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=4, ensure_ascii=False)

    def _get_depot_stats(self, depot_id: str, date_range: Optional[tuple] = None) -> Dict[str, Any]:
        """Calculates comprehensive trading statistics for a depot."""
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if date_range:
            cursor.execute(
                "SELECT * FROM trades WHERE depot_id = ? AND executed_at >= ? AND executed_at <= ? ORDER BY executed_at ASC",
                (depot_id, date_range[0], date_range[1] + " 23:59:59")
            )
        else:
            cursor.execute("SELECT * FROM trades WHERE depot_id = ? ORDER BY executed_at ASC", (depot_id,))

        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()

        sells = [t for t in trades if t.get("trade_type") == "SELL" and t.get("pnl") is not None]
        buys = [t for t in trades if t.get("trade_type") == "BUY"]

        if not sells:
            return {
                "total_buys": len(buys), "total_sells": 0, "win_rate": 0,
                "avg_win": 0, "avg_loss": 0, "expectancy": 0, "profit_factor": 0,
                "max_consecutive_losses": 0, "total_pnl": 0, "best_trade": "-",
                "worst_trade": "-", "trades": trades
            }

        wins = [t for t in sells if float(t["pnl"]) > 0]
        losses = [t for t in sells if float(t["pnl"]) <= 0]

        win_rate = len(wins) / len(sells) * 100 if sells else 0
        avg_win = sum(float(t["pnl"]) for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(float(t["pnl"]) for t in losses) / len(losses)) if losses else 0
        total_pnl = sum(float(t["pnl"]) for t in sells)

        # Expectancy
        expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)

        # Profit Factor
        gross_profit = sum(float(t["pnl"]) for t in wins) if wins else 0
        gross_loss = abs(sum(float(t["pnl"]) for t in losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Max consecutive losses
        max_streak, current_streak = 0, 0
        for t in sells:
            if float(t["pnl"]) <= 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        # Best/worst
        best = max(sells, key=lambda t: float(t["pnl"]))
        worst = min(sells, key=lambda t: float(t["pnl"]))

        return {
            "total_buys": len(buys),
            "total_sells": len(sells),
            "win_rate": round(win_rate, 1),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "expectancy": round(expectancy, 2),
            "profit_factor": round(profit_factor, 2),
            "max_consecutive_losses": max_streak,
            "total_pnl": round(total_pnl, 2),
            "best_trade": f"{best['symbol']} (+{float(best['pnl']):.2f}€, {float(best.get('pnl_pct', 0)):.1f}%)",
            "worst_trade": f"{worst['symbol']} ({float(worst['pnl']):.2f}€, {float(worst.get('pnl_pct', 0)):.1f}%)",
            "trades": trades
        }

    def get_trades(self, depot_id: str, date_prefix: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE depot_id = ? AND executed_at LIKE ? ORDER BY executed_at ASC", (depot_id, f"{date_prefix}%"))
        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return trades
        
    def get_weekly_trades(self, depot_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE depot_id = ? AND executed_at >= ? AND executed_at <= ? ORDER BY executed_at ASC", (depot_id, start_date, end_date + " 23:59:59"))
        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return trades

    def get_todays_missed_alerts(self, today_str: str, traded_symbols: set) -> List[Dict[str, Any]]:
        if not os.path.exists(ALERTS_FILE):
            return []
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                alerts = json.load(f)
            
            missed = []
            for a in alerts:
                if a.get("timestamp", "").startswith(today_str):
                    sym = a.get("symbol", "")
                    if sym not in traded_symbols:
                        missed.append(a)
            return missed
        except Exception:
            return []

    @staticmethod
    def _extract_entry_score(reason: str) -> Optional[float]:
        """Pulls the entry score out of a buy reason. The engines write it as
        'Score 95/100' (daytrader) or 'Alpha 66/100' (short-term)."""
        if not reason:
            return None
        m = re.search(r"(?:Score|Alpha)\s+(\d+(?:\.\d+)?)\s*/\s*100", reason)
        return float(m.group(1)) if m else None

    def _get_entry_score_analysis(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Pairs each SELL with the BUY that opened it and reports how the entry score
        related to the outcome. This is the calibration signal: if winners and losers
        score the same, the threshold is not separating anything."""
        open_buys: Dict[str, List[Optional[float]]] = {}
        paired = []
        for t in sorted(trades, key=lambda x: x.get("executed_at") or ""):
            sym = t.get("symbol")
            if t.get("trade_type") == "BUY":
                open_buys.setdefault(sym, []).append(self._extract_entry_score(t.get("reason", "")))
            elif t.get("trade_type") == "SELL" and t.get("pnl") is not None:
                queue = open_buys.get(sym) or []
                score = queue.pop(0) if queue else None
                if score is not None:
                    paired.append({"symbol": sym, "score": score,
                                   "pnl": float(t["pnl"]),
                                   "pnl_pct": float(t.get("pnl_pct") or 0)})

        if not paired:
            unscored = sum(1 for t in trades if t.get("trade_type") == "BUY"
                           and self._extract_entry_score(t.get("reason", "")) is None)
            return {"paired_trades": 0, "note":
                    f"Keine abgeschlossenen Trades mit Entry-Score im Zeitraum "
                    f"({unscored} Kaeufe ohne Score-Angabe)."}

        wins = [p for p in paired if p["pnl"] > 0]
        losses = [p for p in paired if p["pnl"] <= 0]
        avg = lambda xs: round(sum(x["score"] for x in xs) / len(xs), 1) if xs else None
        return {
            "paired_trades": len(paired),
            "avg_score_winners": avg(wins),
            "avg_score_losers": avg(losses),
            "separation": (round(avg(wins) - avg(losses), 1)
                           if wins and losses else None),
            "detail": sorted(paired, key=lambda p: -p["score"])[:15]
        }

    @staticmethod
    def _load_entry_diagnostics(depot_id: str, days: int = 1) -> Dict[str, Any]:
        """Entry-gate telemetry written by the trading engine on every run."""
        try:
            with open(ENTRY_DIAG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return {}
        out = {}
        for day in sorted(data.keys())[-days:]:
            slot = data[day].get(depot_id)
            if slot:
                out[day] = slot
        return out

    #: Which depot may tune which parameters. On 15.09. the day_trading run changed
    #: short_term_stop_loss_pct, so one depot was turned by two runs on the same night.
    DEPOT_PREFIX = {
        "day_trading": ("daytrade_",),
        "short_term": ("short_term_",),
        "medium_term": ("medium_term_",),
        "long_term": ("long_term_",),
    }

    def _recent_param_changes(self, days: int = 4) -> Dict[str, list]:
        """What was already changed in the last few nights, per parameter.

        Without this the journal sees the same bad all-time statistics every night,
        prescribes the same medicine, and never notices it already did. Between the
        14th and the 16th that ratcheted short_term_stop_atr_mult from 2.5 to 1.75
        and min_alpha from 55 to 70, one step at a time.
        """
        out: Dict[str, list] = {}
        try:
            cutoff = (trading_day() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            conn = sqlite3.connect(DB_FILE)
            rows = conn.execute(
                "SELECT date, param_updates FROM ai_journal "
                "WHERE date >= ? AND param_updates IS NOT NULL ORDER BY id DESC",
                (cutoff,)).fetchall()
            conn.close()
            for date, blob in rows:
                try:
                    changes = json.loads(blob) if isinstance(blob, str) else (blob or {})
                except Exception:
                    continue
                if not isinstance(changes, dict):
                    continue
                for name, delta in changes.items():
                    if isinstance(delta, dict) and "old" in delta and "new" in delta:
                        out.setdefault(name, []).append(
                            {"date": date, "old": delta["old"], "new": delta["new"]})
        except Exception:
            pass
        return out

    def _closed_trades_since(self, depot_id: str, date_str: str) -> int:
        """Closed trades in this depot since a given date - the evidence that has
        accumulated since a parameter was last touched."""
        try:
            conn = sqlite3.connect(DB_FILE)
            n = conn.execute(
                "SELECT COUNT(*) FROM trades WHERE depot_id = ? AND trade_type = 'SELL' "
                "AND pnl IS NOT NULL AND substr(executed_at, 1, 10) > ?",
                (depot_id, date_str)).fetchone()[0]
            conn.close()
            return int(n)
        except Exception:
            return 0

    def format_change_history(self, days: int = PARAM_CHANGE_LOOKBACK_DAYS,
                              depot_id: Optional[str] = None) -> str:
        hist = self._recent_param_changes(days)
        if not hist:
            return "Keine Parameteraenderungen in den letzten Tagen."
        out = []
        for name, entries in sorted(hist.items()):
            chain = " -> ".join(str(e["old"]) for e in reversed(entries))
            chain += f" -> {entries[0]['new']}"
            note = ""
            if depot_id:
                n = self._closed_trades_since(depot_id, entries[0]["date"])
                note = f" | seither {n} abgeschlossene Trades"
                if n < PARAM_CHANGE_MIN_TRADES:
                    note += (f" - unter {PARAM_CHANGE_MIN_TRADES}, eine erneute "
                             f"Aenderung in dieselbe Richtung wird abgelehnt")
            out.append(f"- {name}: {chain} (zuletzt {entries[0]['date']}){note}")
        return chr(10).join(out)

    def _apply_param_updates(self, updates: Dict[str, Any],
                             depot_id: Optional[str] = None) -> Dict[str, Any]:
        """Validates and applies parameter updates from the AI within safety bounds.

        Beyond the static bounds there are three guards, all added after the journal
        tightened the same knobs three nights running and made the depot worse:
        a depot may only tune its own parameters, a parameter may not be moved twice
        in the same direction within the cooldown, and one call may not move it by
        more than a single configured step.

        Returns a dict of what was actually changed.
        """
        if not updates or not isinstance(updates, dict):
            return {}

        current = self._load_strategy()
        history = self._recent_param_changes(PARAM_CHANGE_LOOKBACK_DAYS)
        allowed_prefixes = self.DEPOT_PREFIX.get(depot_id or "", ())
        applied, rejected = {}, {}

        for param_name, new_value in updates.items():
            if param_name not in PARAM_SAFETY_BOUNDS:
                continue  # Unknown parameter, skip

            # Guard 1: stay in your own lane
            if allowed_prefixes and not param_name.startswith(allowed_prefixes):
                rejected[param_name] = (f"gehoert nicht zu Depot {depot_id}")
                continue

            bounds = PARAM_SAFETY_BOUNDS[param_name]
            old_value = current.get(param_name)

            # A parameter that only lives in the engine defaults and has never been
            # written to strategy.json must still be tunable - otherwise every newly
            # introduced knob is silently inert. Fall back to the bounds own type.
            cast_to = type(old_value) if old_value is not None else type(bounds["min"])

            try:
                new_value = cast_to(new_value)
            except (ValueError, TypeError):
                continue

            # Clamp to safety bounds
            new_value = max(bounds["min"], min(bounds["max"], new_value))
            if old_value is None or new_value == old_value:
                if new_value != old_value:
                    current[param_name] = new_value
                    applied[param_name] = {"old": old_value, "new": new_value}
                continue

            direction = 1 if new_value > old_value else -1

            # Guard 2: do not push the same direction again until the previous push
            # has been tested by real trades. Counting days instead of trades let a
            # slow drift walk a parameter to its bound while every single step
            # looked individually justified.
            past = history.get(param_name) or []
            if past:
                last = past[0]
                try:
                    last_dir = 1 if float(last["new"]) > float(last["old"]) else -1
                except (TypeError, ValueError):
                    last_dir = 0
                evidence = self._closed_trades_since(depot_id or "", last["date"])
                if last_dir == direction and evidence < PARAM_CHANGE_MIN_TRADES:
                    rejected[param_name] = (
                        f"seit der Aenderung am {last['date']} ({last['old']} -> "
                        f"{last['new']}) erst {evidence} abgeschlossene Trades; "
                        f"mindestens {PARAM_CHANGE_MIN_TRADES} noetig, um die Wirkung "
                        f"zu beurteilen")
                    continue

            # Guard 3: at most one configured step per run
            step = bounds.get("step")
            if step:
                capped = old_value + direction * step
                if abs(new_value - old_value) > abs(step) * 1.001:
                    new_value = cast_to(max(bounds["min"], min(bounds["max"], capped)))
                # 0.15 - 0.01 lands on 0.13999999999999999 in binary floating point,
                # which then shows up verbatim in the dashboard and the journal entry.
                if isinstance(new_value, float):
                    new_value = round(new_value, 4)
                    rejected[param_name] = (
                        f"Sprung auf eine Schrittweite begrenzt (angefragt wurde mehr)")

            if new_value != old_value:
                current[param_name] = new_value
                applied[param_name] = {"old": old_value, "new": new_value}

        if applied:
            self._save_strategy(current)
        if rejected:
            incidents.record(
                "ai_journal", "param_change_rejected",
                f"Depot {depot_id}: {len(rejected)} Parameteraenderung(en) abgelehnt",
                severity="info", context={"depot": depot_id, "abgelehnt": rejected})
        self._last_rejected = rejected
        return applied


    def already_written_today(self, depot_id: str, mode: str = "daily") -> bool:
        """True if a usable retrospective for this depot/day/mode already exists.

        The database row is an upsert, so a second run looked harmless - but it
        spends another LLM call and, worse, applies another round of parameter
        changes while overwriting the record of the first round. An entry that only
        holds a parse error does not count: that one should be retried.
        """
        try:
            today = trading_day().strftime("%Y-%m-%d")
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute(
                "SELECT reflection FROM ai_journal WHERE depot_id=? AND date=? AND mode=?",
                (depot_id, today, mode)).fetchone()
            conn.close()
            if not row:
                return False
            text = str(row[0] or "")
            failed = ("nicht lesbar" in text or "Fehler beim Parsen" in text or not text.strip())
            return not failed
        except Exception:
            return False

    def generate_retrospective(self, depot_id: str, mode="daily",
                               force: bool = False) -> Dict[str, Any]:
        """Generates an AI retrospective with real statistics and actionable parameter updates."""
        if not self.api_key:
            raise ValueError("Kein Gemini API Key vorhanden.")

        if not force and self.already_written_today(depot_id, mode):
            incidents.record(
                "ai_journal", "duplicate_run_skipped",
                f"{depot_id}/{mode}: Retrospektive fuer heute lag bereits vor - "
                f"zweiter Lauf uebersprungen",
                severity="info", context={"depot": depot_id, "mode": mode})
            raise RuntimeError(
                f"Retrospektive fuer {depot_id} ({mode}) wurde heute bereits erstellt. "
                f"Mit --force erzwingen.")

        now = trading_day()
        today_str = now.strftime("%Y-%m-%d")
        
        # 1. Gather real statistics
        if mode == "weekly":
            start_date = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            stats = self._get_depot_stats(depot_id, date_range=(start_date, today_str))
            date_label = f"{start_date} bis {today_str}"
            period_context = f"Wochenrückblick ({start_date} bis {today_str})"
        else:
            stats = self._get_depot_stats(depot_id, date_range=(today_str, today_str))
            date_label = today_str
            period_context = f"Tagesrückblick ({today_str})"

        # Also get all-time stats for context
        alltime_stats = self._get_depot_stats(depot_id)

        # 2. Load current strategy parameters
        current_params = self._load_strategy()

        # 3. Get missed alerts (daily only)
        traded_symbols = set(t.get("symbol") for t in stats["trades"])
        missed_alerts = self.get_todays_missed_alerts(today_str, traded_symbols) if mode == "daily" else []

        # 3b. Entry-score calibration and gate telemetry
        # Deliberately all-time: a daily window would miss the BUY that opened a
        # position sold today, and one day is never a sample for calibration anyway.
        score_analysis = self._get_entry_score_analysis(alltime_stats["trades"])
        gate_diag = self._load_entry_diagnostics(depot_id, days=7 if mode == "weekly" else 1)

        # Exit analysis deliberately looks far beyond the reporting period. A
        # daily retrospective sees one or two closed trades, and an exit
        # mechanism that fires every second trade and earns nothing is a pattern
        # that only exists across weeks. Judging exits on a single day is how
        # the premature breakeven stop stayed invisible for a month.
        exit_block = exit_analysis.format_for_prompt(depot_id, days=90)

        # 4. Build the bounds description for the prompt
        bounds_desc = "\n".join([
            f"  - {k}: aktuell={current_params.get(k, '?')}, min={v['min']}, max={v['max']}, step={v['step']}"
            for k, v in PARAM_SAFETY_BOUNDS.items()
        ])

        # 5. Build comprehensive prompt with REAL data
        prompt = f"""Du bist ein professioneller Quant-Analyst und Trading-Coach. Du analysierst die Performance 
eines algorithmischen Trading-Systems und schlägst KONKRETE Parameteränderungen vor.

## {period_context} — Depot: {depot_id}

### Heutige/Wöchentliche Statistiken:
- Abgeschlossene Trades (SELL): {stats['total_sells']}
- Win-Rate: {stats['win_rate']}%
- Durchschn. Gewinn pro Gewinner: {stats['avg_win']}€
- Durchschn. Verlust pro Verlierer: {stats['avg_loss']}€
- Expectancy pro Trade: {stats['expectancy']}€
- Profit Factor: {stats['profit_factor']}
- Gesamt-PnL: {stats['total_pnl']}€
- Max. Verluststrecke: {stats['max_consecutive_losses']} Trades in Folge
- Bester Trade: {stats['best_trade']}
- Schlechtester Trade: {stats['worst_trade']}

### Gesamtstatistik (seit Depotstart):
- Abgeschlossene Trades: {alltime_stats['total_sells']}
- Win-Rate: {alltime_stats['win_rate']}%
- Expectancy: {alltime_stats['expectancy']}€/Trade
- Profit Factor: {alltime_stats['profit_factor']}
- Gesamt-PnL: {alltime_stats['total_pnl']}€
- Max. Verluststrecke: {alltime_stats['max_consecutive_losses']}

### BEREITS VORGENOMMENE PARAMETERAENDERUNGEN (letzte Tage):
{self.format_change_history(depot_id=depot_id)}
Drehe einen Parameter NICHT erneut in dieselbe Richtung, solange die letzte
Aenderung nicht durch neue Trades geprueft wurde. Massstab sind abgeschlossene
Trades, nicht verstrichene Tage - solche Vorschlaege werden automatisch abgelehnt.
Fehlt die Evidenz, ist "nichts aendern" die richtige Antwort.

### HARTE RANDBEDINGUNG DES SYSTEMS (nicht verhandelbar):
Der Handels-Bot laeuft als Cron-Job und prueft die Positionen bestenfalls alle
5 Minuten, bei Warteschlangen auch deutlich seltener. Dazwischen kann NICHTS
verkauft werden. Ein Stop von X% auf einem Hebelzertifikat haelt daher nur, wenn
der Basiswert mehr als X%/Hebel Gegenbewegung braucht, um ihn zu ueberspringen.
Bei Hebel 7-10 liegt diese Schwelle bei 1,4-2,0% - genau die Groessenordnung, die
der Scanner als Einstiegssignal sucht. Der Hebel ist deshalb auf 3x begrenzt.
Schlage NIEMALS einen hoeheren Hebel vor, auch nicht zur Renditesteigerung, und
begruende Verluste nicht mit "zu wenig Hebel". Wenn die Verluste zu gross sind,
ist der richtige Hebel kleiner, nicht groesser.

Der Breakeven-Trigger des Kurzfristdepots stand bis zum 23.09.2026 bei 1.0 ATR.
Das hat die Stops auf den Einstand gezogen, bevor die Trades irgendwo waren: drei
so beendete Positionen stiegen danach im Schnitt 14%, die Haelfte aller Ausstiege
lag im Nullsummenbereich. Er steht jetzt bei 2.0 und die Untergrenze bei 1.5.
Senke ihn nicht mit der Begruendung, Verluste zu begrenzen - der Wert begrenzt
keine Verluste, er beendet Gewinner vorzeitig. Niedrigere Vorschlaege werden
abgelehnt.

### TECHNISCHE STOERUNGEN (Defekte, keine Strategiefrage):
{incidents.summarize(7)}
Wenn ein Verlust auf eine technische Stoerung zurueckgeht, ist die Antwort NICHT,
Parameter zu drehen. Benenne den Defekt in "reflection" und lass die Parameter in Ruhe.

### Aktuelle Strategie-Parameter:
{json.dumps(current_params, indent=2)}

### Erlaubte Parameterbereiche (Sicherheitsgrenzen):
{bounds_desc}

### Einzelne Trades im Zeitraum:
{json.dumps([{
    'type': t.get('trade_type'), 'symbol': t.get('symbol'), 'pnl': t.get('pnl'),
    'pnl_pct': t.get('pnl_pct'), 'reason': t.get('reason', '')[:100], 'date': t.get('executed_at')
} for t in stats['trades'][:30]], indent=2, ensure_ascii=False)}

### AUSSTIEGSANALYSE (wie Trades endeten - und was der Kurs DANACH tat):
{exit_block}
Lesehilfe und Pflichtpruefung:
- "kurs_nach_ausstieg_schnitt_pct" ist die Kursentwicklung NACH dem Verkauf, gemessen
  ab dem Verkaufspreis ueber die folgenden Handelstage. Positiv heisst: die Position
  lief ohne uns weiter. Das ist die einzige Zahl, die einen gelungenen Ausstieg von
  einem verfruehten unterscheidet - im PnL sehen beide gleich aus.
- Ein Ausstiegsgrund mit vielen Treffern, einem Ergebnis nahe null UND deutlich
  positiver Nachentwicklung ist ein DEFEKT DER AUSSTIEGSLOGIK, kein Einstiegsproblem.
  Eine hoehere Einstiegshuerde behebt ihn nicht. Benenne ihn in "reflection" und setze
  am zugehoerigen Ausstiegsparameter an (Breakeven-Trigger, Trailing-Abstand,
  Thesen-Schwelle) statt an min_entry_score.
- Umgekehrt: sind die Nachentwicklungen ueberwiegend negativ, haben die Stops ihre
  Aufgabe erfuellt. Dann ist der Fehler im Einstieg zu suchen, nicht im Ausstieg.
- "nullsummen_ausstiege" zaehlt Trades, die praktisch auf dem Einstand endeten. Ein
  hoher Anteil bedeutet, dass das System Positionen loslaesst, bevor sie etwas
  erreichen konnten - auch dann, wenn die Win-Rate dadurch harmlos aussieht.

### Verpasste Signale (nicht gehandelt):
{json.dumps(missed_alerts[:10], indent=2, ensure_ascii=False) if missed_alerts else "Keine verpassten Signale."}

### Entry-Score-Kalibrierung seit Depotstart (Score beim Kauf vs. Ergebnis):
{json.dumps(score_analysis, indent=2, ensure_ascii=False)}

### Entry-Gate-Telemetrie (warum wurde gehandelt bzw. NICHT gehandelt):
{json.dumps(gate_diag, indent=2, ensure_ascii=False) if gate_diag else "Keine Telemetrie vorhanden."}
Lesehilfe: "runs" = Bot-Durchlaeufe, "scored" = bewertete Kandidaten, "best_score" =
bester an diesem Tag erreichter Score, "above_threshold" = wie oft die Huerde
uebersprungen wurde, "blocks" = welches Gate wie oft blockiert hat.

## Deine Aufgabe:
1. Analysiere die Performance-Daten. Was sind die konkreten Schwachstellen?
2. Schlage KONKRETE Parameteränderungen vor, die die Expectancy verbessern.
   - Wenn die Win-Rate zu niedrig ist: Erhöhe den min_entry_score.
   - Wenn die Verluste zu groß sind: Senke den stop_loss_pct oder den max_leverage.
   - Wenn zu wenig gehandelt wird: Senke den min_entry_score oder erhöhe max_daily_trades.
   - Wenn der Profit Factor < 1.0: Die Strategie verliert Geld — aggressive Anpassung nötig.
3. Wenn keine Trades stattfanden: Nutze die Entry-Gate-Telemetrie, um das zu erklaeren.
   - "above_threshold": 0 bei vielen "scored" heisst: die Huerde ist zu hoch angesetzt.
   - Liegt "best_score" ueber viele Durchlaeufe DAUERHAFT unter "threshold", ist die
     Huerde strukturell unerreichbar. Das ist ein Defekt, kein Marktzustand - melde es
     deutlich in "reflection" und senke die Huerde Richtung des beobachteten best_score.
   - Dominiert ein einzelner Eintrag in "blocks", nenne ihn explizit beim Namen.
4. Pruefe die Entry-Score-Kalibrierung:
   - "separation" deutlich > 0 heisst, der Score trennt Gewinner von Verlierern - dann
     lohnt es, die Huerde anzuheben.
   - "separation" um 0 oder negativ heisst, der Score sagt nichts vorher. Dann bringt
     eine hoehere Huerde NICHTS ausser weniger Trades; setze stattdessen an Stop- und
     Risikoparametern an und weise in "lesson" darauf hin.
5. Werte die Ausstiegsanalyse aus, BEVOR du Einstiegsparameter anfasst. Die Frage
   "haben wir die richtigen Trades gekauft?" und die Frage "haben wir sie zur
   richtigen Zeit verkauft?" haben getrennte Antworten und getrennte Stellschrauben.
   Ein Verlust, der nach dem Verkauf wieder aufgeholt wurde, war kein Einstiegsfehler.
6. Ändere Parameter NUR wenn du eine klare datengetriebene Begründung hast. Wenn alles gut läuft, ändere NICHTS.

Antworte AUSSCHLIESSLICH im folgenden JSON-Format (keine Markdown-Blöcke):
{{
  "reflection": "Deine detaillierte Analyse der Trades und Schwachstellen...",
  "missed_opportunities": "Analyse der verpassten Signale und ob sie profitabel gewesen wären...",
  "lesson": "Die konkrete, datengetriebene Lektion...",
  "parameter_changes": {{
    "parameter_name": neuer_wert,
    "parameter_name2": neuer_wert2
  }},
  "change_reasoning": "Warum genau diese Parameter geändert werden, mit Bezug auf die Statistiken..."
}}

WICHTIG: "parameter_changes" muss ein JSON-Objekt sein mit den exakten Parameternamen aus strategy.json.
Wenn keine Änderungen nötig sind, setze "parameter_changes": {{}}.
"""

        # 6. Call Gemini
        response = None
        last_err = None
        
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as e:
            raise Exception(f"Konnte Modell-Liste nicht abrufen. API-Key ungültig? Fehler: {e}")

        if not available_models:
            raise Exception("Dein API-Key hat Zugriff auf 0 Modelle.")

        # Prioritize 2.0/1.5 models
        available_models.sort(key=lambda x: ('2.0' in x, '1.5' in x), reverse=True)

        for m_name in available_models[:5]:  # Try up to 5 models
            try:
                if '1.5' in m_name or '2.0' in m_name:
                    temp_model = genai.GenerativeModel(m_name, generation_config={"response_mime_type": "application/json"})
                else:
                    temp_model = genai.GenerativeModel(m_name)
                response = temp_model.generate_content(prompt)
                if response and response.text:
                    break
            except Exception as e:
                last_err = e
                response = None
                
        if not response:
            raise Exception(f"Alle {len(available_models)} Modelle fehlgeschlagen. Letzter Fehler: {last_err}")

        # 7. Parse response
        raw_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
        res_json = parse_model_json(raw_text)

        if res_json is None:
            # Preserve the evidence. The 17.09. incident kept only the first 300
            # characters, and the 23.09. failure sat at character 3944 - so the
            # log recorded that something broke without recording what. The full
            # answer goes to disk, the log points at it.
            stamp = get_berlin_now().strftime("%Y%m%d-%H%M%S")
            dump_path = data_file(f"llm_raw_{depot_id}_{mode}_{stamp}.txt")
            try:
                with open(dump_path, "w", encoding="utf-8") as fh:
                    fh.write(raw_text)
                saved = os.path.basename(dump_path)
            except Exception:
                saved = "konnte nicht gespeichert werden"
            incidents.record(
                "ai_journal", "llm_parse_error",
                "Antwort des Modells war auch nach allen Reparaturversuchen kein "
                "gueltiges JSON",
                severity="error",
                context={"depot": depot_id, "mode": mode, "rohantwort": saved,
                         "laenge": len(raw_text),
                         "antwort_anfang": str(raw_text)[:300]})
            res_json = {
                "reflection": ("Antwort des Modells nicht lesbar. Die Stoerung ist "
                               f"im Stoerungs-Log vermerkt, die Rohantwort liegt "
                               f"unter {saved}."),
                "missed_opportunities": "",
                "lesson": "",
                "parameter_changes": {},
                "change_reasoning": ""
            }

        # 8. Apply parameter changes (the core new feature!)
        param_changes = res_json.get("parameter_changes", {})
        applied_changes = self._apply_param_updates(param_changes, depot_id=depot_id)
        change_reasoning = res_json.get("change_reasoning", "")

        if applied_changes:
            param_log = "; ".join([f"{k}: {v['old']} -> {v['new']}" for k, v in applied_changes.items()])
            print(f"  ✅ PARAMETER ANGEPASST: {param_log}")
            print(f"  📝 Begründung: {change_reasoning[:200]}")
        else:
            print(f"  ℹ️ Keine Parameteränderungen vorgenommen.")

        # 9. Save journal entry
        def _safe_str(val):
            if isinstance(val, (dict, list)):
                return json.dumps(val, ensure_ascii=False)
            return str(val) if val else ""

        journal_entry = {
            "depot_id": depot_id,
            "date": date_label,
            "mode": mode,
            "win_rate": round(alltime_stats["win_rate"], 2),
            "best_trade": stats["best_trade"],
            "worst_trade": stats["worst_trade"],
            "reflection": _safe_str(res_json.get("reflection", "")),
            "missed_opportunities": _safe_str(res_json.get("missed_opportunities", "")),
            "lesson": _safe_str(res_json.get("lesson", "")),
            "param_updates": _safe_str(applied_changes) if applied_changes else _safe_str(param_changes)
        }

        self.save_journal_entry(journal_entry)
        return journal_entry

    def save_journal_entry(self, entry: Dict[str, Any]):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_journal (depot_id, date, mode, win_rate, best_trade, worst_trade, reflection, lesson, missed_opportunities, param_updates)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(depot_id, date, mode) DO UPDATE SET
                win_rate=excluded.win_rate,
                best_trade=excluded.best_trade,
                worst_trade=excluded.worst_trade,
                reflection=excluded.reflection,
                lesson=excluded.lesson,
                missed_opportunities=excluded.missed_opportunities,
                param_updates=excluded.param_updates
        ''', (
            entry["depot_id"], entry["date"], entry.get("mode", "daily"), entry["win_rate"], entry["best_trade"], entry["worst_trade"],
            entry["reflection"], entry["lesson"], entry["missed_opportunities"], entry.get("param_updates", "{}")
        ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_journals():
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Verify table exists first
        try:
            cursor.execute("SELECT * FROM ai_journal ORDER BY date DESC")
            rows = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            rows = []
        conn.close()
        return rows
