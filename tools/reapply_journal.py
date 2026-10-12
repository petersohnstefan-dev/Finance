"""Einen bereits berechneten Tagebucheintrag erneut auf den frischen Stand schreiben.

Hintergrund: data/portfolio.db ist eine SQLite-Datei und damit binaer. Git kann
sie nicht zusammenfuehren. Der Handels-Bot pusht werktags alle fuenf Minuten; ist
die naechtliche Retrospektive fertig, liegt auf origin meist schon eine neuere
Datenbank. Der Push wird abgelehnt, das Retry im Workflow macht
`git pull --rebase`, und das endet zwangslaeufig so:

    Cannot merge binary files: data/portfolio.db
    CONFLICT (content): Merge conflict in data/portfolio.db
    error: could not apply ... Retrospektive + Strategie-Optimierung

Am 02.10.2026 ist dabei eine fertig berechnete Wochenretrospektive fuer beide
Depots verlorengegangen - nicht weil das Modell versagt haette, sondern weil der
einzige Weg zurueck in die Datenbank ein Rebase war, der nie gelingen konnte.

Statt zu rebasen setzt der Workflow jetzt hart auf origin/main zurueck und
schreibt den Eintrag mit diesem Skript neu. Der Eintrag liegt dafuer in
data/journal_pending/ - unversioniert, damit `git reset --hard` ihn nicht
mitnimmt. Die Speicherung ist ein Upsert auf (depot_id, date, mode), ein
erneutes Anwenden also gefahrlos.

    python tools/reapply_journal.py            # alle offenen Eintraege
    python tools/reapply_journal.py --clear    # danach aufraeumen
"""
import argparse
import glob
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.paths import data_file  # noqa: E402

PENDING_DIR = data_file("journal_pending")


def _pending_dateien():
    return sorted(glob.glob(os.path.join(PENDING_DIR, "*.json")))


def _eintrag_schreiben(conn: sqlite3.Connection, e: dict) -> None:
    conn.execute(
        "INSERT INTO ai_journal (depot_id, date, mode, win_rate, best_trade, "
        "worst_trade, reflection, lesson, missed_opportunities, param_updates) "
        "VALUES (?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(depot_id, date, mode) DO UPDATE SET "
        "win_rate=excluded.win_rate, best_trade=excluded.best_trade, "
        "worst_trade=excluded.worst_trade, reflection=excluded.reflection, "
        "lesson=excluded.lesson, missed_opportunities=excluded.missed_opportunities, "
        "param_updates=excluded.param_updates",
        (e["depot_id"], e["date"], e.get("mode", "daily"), e.get("win_rate"),
         e.get("best_trade"), e.get("worst_trade"), e.get("reflection"),
         e.get("lesson"), e.get("missed_opportunities"),
         e.get("param_updates", "{}")))


def _strategie_anwenden(updates: dict) -> int:
    """Die vom Lauf bereits durchgesetzten Parameterwerte erneut setzen.

    Nach `git reset --hard` steht in strategy.json wieder der Stand von origin.
    Die Sicherheitspruefungen sind beim urspruenglichen Lauf schon gelaufen -
    hier werden nur die Ergebnisse wiederhergestellt, nicht neu entschieden.
    """
    if not updates:
        return 0
    pfad = data_file("strategy.json")
    try:
        with open(pfad, encoding="utf-8") as fh:
            strat = json.load(fh)
    except Exception:
        return 0
    n = 0
    for name, wert in updates.items():
        if strat.get(name) != wert:
            strat[name] = wert
            n += 1
    if n:
        with open(pfad, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(strat, fh, indent=4, ensure_ascii=False)
            fh.write("\n")
    return n


def main() -> int:
    p = argparse.ArgumentParser(description="Offene Tagebucheintraege neu schreiben")
    p.add_argument("--clear", action="store_true",
                   help="offene Eintraege nach dem Schreiben entfernen")
    args = p.parse_args()

    dateien = _pending_dateien()
    if not dateien:
        print("Keine offenen Tagebucheintraege.")
        return 0

    conn = sqlite3.connect(data_file("portfolio.db"))
    geschrieben = params = 0
    for f in dateien:
        try:
            with open(f, encoding="utf-8") as fh:
                daten = json.load(fh)
            _eintrag_schreiben(conn, daten["entry"])
            geschrieben += 1
            params += _strategie_anwenden(daten.get("strategy_updates") or {})
            e = daten["entry"]
            print(f"  erneut geschrieben: {e['depot_id']} / {e['date']} ({e.get('mode')})")
        except Exception as exc:
            print(f"  FEHLER bei {os.path.basename(f)}: {exc}", file=sys.stderr)
    conn.commit()
    conn.close()

    print(f"{geschrieben} Eintrag/Eintraege geschrieben, "
          f"{params} Strategie-Werte wiederhergestellt.")
    if args.clear:
        for f in dateien:
            try:
                os.remove(f)
            except Exception:
                pass
        print("Offene Eintraege entfernt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
