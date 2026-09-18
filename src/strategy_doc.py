"""Renders live strategy values for the handbook.

The handbook used to have its numbers typed in by hand, so every parameter the
learning journal tuned overnight silently made the documentation wrong: it still
promised an alpha threshold of 55 while 65 was active, and there was no mechanism
that would ever have corrected it (update_handbook.py is a one-off dev script
that nothing calls).

These helpers read data/strategy.json at render time, so a value shown in the
handbook is by construction the value the engine uses. Each one also reports
whether the journal has recently changed it.
"""
import datetime
import json
import sqlite3
from typing import Any, Dict, List, Optional

from src.paths import data_file


def load_strategy() -> Dict[str, Any]:
    try:
        with open(data_file("strategy.json"), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def val(key: str, default: Any = None) -> Any:
    return load_strategy().get(key, default)


def pct(key: str, default: float = 0.0, digits: int = 0) -> str:
    """A fraction stored as 0.15 rendered as '15 %'."""
    v = load_strategy().get(key, default)
    try:
        return f"{float(v) * 100:.{digits}f} %".replace(".", ",")
    except (TypeError, ValueError):
        return "—"


def raw_pct(key: str, default: float = 0.0, digits: int = 1) -> str:
    """A value already stored as a percentage (e.g. 1.5 meaning 1.5%)."""
    v = load_strategy().get(key, default)
    try:
        return f"{float(v):.{digits}f} %".replace(".", ",")
    except (TypeError, ValueError):
        return "—"


def num(key: str, default: Any = None, digits: int = 0) -> str:
    v = load_strategy().get(key, default)
    try:
        f = float(v)
        if digits == 0 and f == int(f):
            return str(int(f))
        return f"{f:.{digits}f}".replace(".", ",")
    except (TypeError, ValueError):
        return "—"


def recent_changes(days: int = 14) -> List[Dict[str, Any]]:
    """Parameter changes the journal made, newest first."""
    out: List[Dict[str, Any]] = []
    try:
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        conn = sqlite3.connect(data_file("portfolio.db"))
        rows = conn.execute(
            "SELECT date, depot_id, param_updates FROM ai_journal "
            "WHERE date >= ? AND param_updates IS NOT NULL AND param_updates != '{}' "
            "ORDER BY id DESC", (cutoff,)).fetchall()
        conn.close()
        for date, depot, blob in rows:
            try:
                changes = json.loads(blob) if isinstance(blob, str) else (blob or {})
            except Exception:
                continue
            for name, delta in (changes or {}).items():
                if isinstance(delta, dict) and "old" in delta:
                    out.append({"date": date, "depot": depot, "param": name,
                                "old": delta["old"], "new": delta["new"]})
    except Exception:
        pass
    return out


def last_changed(key: str, days: int = 14) -> Optional[str]:
    for c in recent_changes(days):
        if c["param"] == key:
            return c["date"]
    return None
