"""Technical incident log - defects, not strategy.

The learning journal is a strategy retrospective: it sees a bad result and turns
parameters. That is the wrong instrument for a defect. On 17.09. a knock-out on a
0.03 USD underlying lost 1570 EUR because the certificate maths collapsed, and the
journal's answer over the preceding nights had been to tighten the stop - which,
through `position = risk / stop_distance`, made the position *larger*.

So defects are recorded here instead: what happened, which component, how bad, and
enough context to reproduce it. The journal reads this log and is told to fix the
defect rather than tune around it.
"""
import datetime
import json
import os
from typing import Any, Dict, List, Optional

from src.paths import data_file

INCIDENT_FILE = data_file("incidents.json")
MAX_INCIDENTS = 400

#: severity -> meaning
SEVERITIES = ("info", "warn", "error", "critical")


def _now() -> str:
    try:
        from src.market_seasonality import get_berlin_now
        return get_berlin_now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def record(component: str, kind: str, message: str,
           severity: str = "warn", context: Optional[Dict[str, Any]] = None) -> None:
    """Appends one incident. Never raises - logging must not break trading.

    component: where it happened ("derivatives", "ai_journal", "tribunal", ...)
    kind:      stable slug for grouping ("invalid_certificate", "llm_parse_error", ...)
    """
    try:
        entries: List[Dict[str, Any]] = []
        if os.path.exists(INCIDENT_FILE):
            with open(INCIDENT_FILE, "r", encoding="utf-8") as fh:
                entries = json.load(fh)

        entry = {
            "timestamp": _now(),
            "component": component,
            "kind": kind,
            "severity": severity if severity in SEVERITIES else "warn",
            "message": str(message)[:600],
            "context": context or {},
        }

        # Collapse repeats: the bot runs every five minutes, and an unresolved
        # defect would otherwise bury everything else within a day.
        for prev in entries[:6]:
            if (prev.get("component") == component and prev.get("kind") == kind
                    and prev.get("message") == entry["message"]):
                prev["count"] = int(prev.get("count", 1)) + 1
                prev["last_seen"] = entry["timestamp"]
                break
        else:
            entry["count"] = 1
            entry["last_seen"] = entry["timestamp"]
            entries.insert(0, entry)

        entries = entries[:MAX_INCIDENTS]
        os.makedirs(os.path.dirname(INCIDENT_FILE), exist_ok=True)
        with open(INCIDENT_FILE, "w", encoding="utf-8") as fh:
            json.dump(entries, fh, indent=1, ensure_ascii=False)
    except Exception:
        pass


def get_recent(limit: int = 50, min_severity: str = "info") -> List[Dict[str, Any]]:
    try:
        with open(INCIDENT_FILE, "r", encoding="utf-8") as fh:
            entries = json.load(fh)
    except Exception:
        return []
    floor = SEVERITIES.index(min_severity) if min_severity in SEVERITIES else 0
    return [e for e in entries
            if SEVERITIES.index(e.get("severity", "warn")) >= floor][:limit]


def summarize(days: int = 7) -> str:
    """Compact text for the journal prompt and the dashboard."""
    entries = get_recent(200)
    if not entries:
        return "Keine technischen Stoerungen protokolliert."
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    recent = [e for e in entries if str(e.get("timestamp", ""))[:10] >= cutoff]
    if not recent:
        return f"Keine technischen Stoerungen in den letzten {days} Tagen."

    by_kind: Dict[str, Dict[str, Any]] = {}
    for e in recent:
        key = f"{e['component']}/{e['kind']}"
        slot = by_kind.setdefault(key, {"count": 0, "severity": e.get("severity", "warn"),
                                        "last": e.get("last_seen", e["timestamp"]),
                                        "message": e.get("message", "")})
        slot["count"] += int(e.get("count", 1))
        if SEVERITIES.index(e.get("severity", "warn")) > SEVERITIES.index(slot["severity"]):
            slot["severity"] = e.get("severity", "warn")

    lines = [f"{len(recent)} Stoerungsmeldungen in den letzten {days} Tagen:"]
    for key, s in sorted(by_kind.items(),
                         key=lambda kv: (-SEVERITIES.index(kv[1]["severity"]), -kv[1]["count"])):
        lines.append(f"- [{s['severity'].upper()}] {key}: {s['count']}x, zuletzt "
                     f"{s['last']}. {s['message'][:200]}")
    return "\n".join(lines)
