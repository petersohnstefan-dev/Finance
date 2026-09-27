"""Wöchentlicher Vervielfacher-Scan.

Läuft sonntags: die Eingangsdaten sind Jahresabschlüsse, die sich höchstens
vierteljährlich ändern, und am Wochenende konkurriert der Lauf mit keinem
Handels-Job um die yfinance-Anbindung.

    python run_tenbagger_scan.py                  # voller Lauf, speichert
    python run_tenbagger_scan.py --dry-run        # rechnet, speichert nicht
    python run_tenbagger_scan.py --limit 150      # kurzer Testlauf
    python run_tenbagger_scan.py --symbols AAON,ODD
"""
import argparse
import json
import sys
import time
from datetime import datetime

from src import incidents
from src.tenbagger import (BAND_WATCH, get_scan_dates, run_scan, save_scan)


def main() -> int:
    p = argparse.ArgumentParser(description="Vervielfacher-Scan")
    p.add_argument("--dry-run", action="store_true",
                   help="nur rechnen, nichts in die Datenbank schreiben")
    p.add_argument("--limit", type=int, default=None,
                   help="nur die ersten N Symbole prüfen (Testlauf)")
    p.add_argument("--symbols", type=str, default=None,
                   help="Kommaliste statt des ganzen Universums")
    p.add_argument("--min-score", type=int, default=BAND_WATCH)
    p.add_argument("--workers", type=int, default=None,
                   help="Parallele Abrufe (Standard 2 - Yahoo drosselt)")
    p.add_argument("--budget", type=int, default=None,
                   help="Wie viele Werte dieser Lauf neu abruft (Standard 220)")
    args = p.parse_args()

    symbole = None
    if args.symbols:
        symbole = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    elif args.limit:
        from src.tenbagger_universe import get_universe
        symbole = get_universe()["symbole"][:args.limit]

    start = time.time()
    print(f"Vervielfacher-Scan gestartet {datetime.now():%Y-%m-%d %H:%M:%S}")
    try:
        from src.tenbagger import DEFAULT_WORKERS, MAX_REFRESHES_PER_RUN
        ergebnis = run_scan(symbole=symbole,
                            max_workers=args.workers or DEFAULT_WORKERS,
                            min_score=args.min_score,
                            budget=args.budget or MAX_REFRESHES_PER_RUN)
    except Exception as e:
        incidents.record("tenbagger", "scan_failed",
                         f"Vervielfacher-Scan abgebrochen: {str(e)[:200]}",
                         severity="error")
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1

    treffer = ergebnis["treffer"]
    dauer = time.time() - start
    uni = ergebnis.get("universum", {})
    print()
    print(f"  Universum      {ergebnis['geprueft']} Symbole ({uni.get('herkunft', '?')})")
    print(f"  Quellen        {json.dumps(uni.get('quellen', {}), ensure_ascii=False)}")
    print(f"  Cache          {ergebnis['im_cache']} Bewertungen, "
          f"{ergebnis['faellig']} fällig, {ergebnis['neu_geholt']} neu geholt")
    print(f"  aussortiert    zu groß {ergebnis['zu_gross']}, "
          f"ohne Daten {ergebnis['ohne_daten']}, dünne Daten {ergebnis['duenne_daten']}")
    if ergebnis.get("leer_abgerufen"):
        print(f"  leer abgerufen {ergebnis['leer_abgerufen']} "
              f"(Drosselung durch Yahoo)")
    print(f"  gelistet       {len(treffer)}")
    print(f"  Dauer          {dauer/60:.1f} Minuten")

    if treffer:
        print()
        print(f"  {'Rang':<5}{'Symbol':<10}{'Score':>6}{'Motor':>7}{'Größe':>7}"
              f"{'Abzug':>7}{'Mrd €':>9}  Name")
        for i, r in enumerate(treffer[:20], start=1):
            print(f"  {i:<5}{r['symbol']:<10}{r['score']:>6}{r['motorscore']:>7}"
                  f"{r['groessenfaktor']:>7.2f}{r['abzugsfaktor']:>7.2f}"
                  f"{str(r['marktkap_mrd_eur']):>9}  {r['name'][:28]}")

    # A scan that finds nothing is either a very unusual market or a defect, and
    # the difference matters enough to be logged rather than to pass silently.
    if ergebnis.get("leer_abgerufen", 0) > max(20, ergebnis.get("neu_geholt", 0)):
        incidents.record(
            "tenbagger", "rate_limited",
            f"Yahoo hat den Vervielfacher-Scan gedrosselt: "
            f"{ergebnis['leer_abgerufen']} leere Abrufe gegen "
            f"{ergebnis['neu_geholt']} erfolgreiche. Die Liste stammt aus dem "
            f"Zwischenspeicher, fehlgeschlagene Abrufe wurden nicht übernommen.",
            severity="warn", context={k: v for k, v in ergebnis.items() if k != "treffer"})

    if not treffer:
        incidents.record("tenbagger", "scan_empty",
                         f"Vervielfacher-Scan ohne einen einzigen Treffer "
                         f"({ergebnis['im_cache']} Bewertungen im Zwischenspeicher)",
                         severity="warn",
                         context={k: v for k, v in ergebnis.items() if k != "treffer"})

    if args.dry_run:
        print("\n  --dry-run: nichts gespeichert.")
        return 0

    n = save_scan(treffer)
    tage = get_scan_dates()
    print(f"\n  {n} Einträge gespeichert. Historie umfasst jetzt {len(tage)} Läufe "
          f"(seit {tage[-1] if tage else '-'}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
