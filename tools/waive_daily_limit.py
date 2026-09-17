#!/usr/bin/env python
"""Excludes a loss from today's daily loss limit.

For losses caused by a defect rather than by the strategy. The limit exists to
stop a losing strategy; a broken instrument says nothing about the strategy. The
trade stays in the history, in the win/loss statistics and in the incident log -
only the block on further trading for the rest of the day is lifted.

    python tools/waive_daily_limit.py day_trading 1570.04 "Grund"
    python tools/waive_daily_limit.py --show
"""
import json
import sys

from src.paths import data_file
from src.portfolio import get_berlin_now
from src import incidents

PORTFOLIO_FILE = data_file("portfolios.json")


def load():
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save(data):
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def show():
    data = load()
    waivers = data.get("daily_limit_waivers") or {}
    if not waivers:
        print("Keine Ausnahmen eingetragen.")
        return
    today = get_berlin_now().strftime("%Y-%m-%d")
    for depot, entries in waivers.items():
        for w in entries:
            state = "AKTIV" if w.get("date") == today else "abgelaufen"
            print(f"  [{state}] {depot} {w.get('date')}: {w.get('amount'):+.2f} EUR - "
                  f"{w.get('reason', '')}")


def main() -> int:
    if "--show" in sys.argv:
        show()
        return 0
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    depot = sys.argv[1]
    try:
        amount = abs(float(sys.argv[2]))
    except ValueError:
        print(f"Betrag nicht lesbar: {sys.argv[2]}", file=sys.stderr)
        return 2
    reason = sys.argv[3] if len(sys.argv) > 3 else "Technischer Defekt"

    data = load()
    if depot not in data.get("portfolios", {}):
        print(f"Unbekanntes Depot: {depot}", file=sys.stderr)
        return 2

    today = get_berlin_now().strftime("%Y-%m-%d")
    waivers = data.setdefault("daily_limit_waivers", {}).setdefault(depot, [])
    # Keep only today's - older ones have expired anyway
    waivers[:] = [w for w in waivers if w.get("date") == today]
    waivers.append({
        "date": today,
        "amount": round(amount, 2),
        "reason": reason,
        "created": get_berlin_now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save(data)

    incidents.record(
        "portfolio", "daily_limit_waived",
        f"{depot}: {amount:.2f} EUR vom Tages-Verlustlimit ausgenommen - {reason}",
        severity="info",
        context={"depot": depot, "betrag": round(amount, 2), "datum": today,
                 "hinweis": "Trade bleibt in Historie und Statistik enthalten"})

    print(f"{depot}: {amount:.2f} EUR fuer {today} vom Tageslimit ausgenommen.")
    print(f"Grund: {reason}")
    print("Der Trade bleibt in Historie und Trefferquote sichtbar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
