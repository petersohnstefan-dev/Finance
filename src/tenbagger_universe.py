"""Das Suchfeld für die Vervielfacher-Suche - dort, wo kleine Werte stehen.

The trading universe this app runs on was assembled for a different job: names
liquid enough to carry a knock-out certificate and to be traded intraday. Measured
against it, the tenbagger question has almost nowhere to look - 101 of 318 priced
members are above 100 billion euros, where a tenfold rise would make them among
the largest companies on earth, and only 87 sit at or below 5 billion.

So the scan gets its own universe, drawn from the small- and mid-cap indices where
a tenbagger can still mathematically happen. The lists come from Wikipedia, which
is free, has no key, and is maintained by people who care about index changes.
They are cached on disk for a month; a failed fetch falls back to the last cached
copy and then to the trading universe, and the caller is always told which of the
three it got rather than being handed a list of unknown age.
"""
from __future__ import annotations

import io
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.paths import data_file

CACHE_FILE = data_file("tenbagger_universe.json")

#: Index lists are revised a few times a year; a month is short enough to catch
#: that and long enough not to hammer Wikipedia on every scan.
REFRESH_AFTER_DAYS = 30

USER_AGENT = "FinanceDashboard/1.0 (privates Musterdepot-Projekt)"

#: (label, URL, suffix for yfinance). The suffix is what turns the German index
#: symbol AIXA into the ticker AIXA.DE that yfinance can price.
QUELLEN = [
    ("S&P 600 SmallCap", "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies", ""),
    ("S&P 400 MidCap", "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies", ""),
    ("MDAX", "https://en.wikipedia.org/wiki/MDAX", ".DE"),
    ("TecDAX", "https://de.wikipedia.org/wiki/TecDAX", ".DE"),
]


def _hole_liste(url: str, suffix: str) -> List[str]:
    """Ticker column of the first table on the page that has one."""
    import pandas as pd
    import requests

    antwort = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    antwort.raise_for_status()
    for tabelle in pd.read_html(io.StringIO(antwort.text)):
        spalten = [c for c in tabelle.columns
                   if any(w in str(c).lower() for w in ("ticker", "symbol"))]
        if not spalten or len(tabelle) < 20:
            continue
        roh = [str(x).strip().upper() for x in tabelle[spalten[0]].dropna()]
        sauber = []
        for s in roh:
            s = s.split("[")[0].strip()          # Wikipedia footnote markers
            if not s or len(s) > 8 or s in ("NAN", "-"):
                continue
            # yfinance writes class shares with a dash, Wikipedia with a dot
            sauber.append(s.replace(".", "-") + suffix if not suffix else s + suffix)
        if sauber:
            return sauber
    return []


def _lade_cache() -> Optional[Dict[str, Any]]:
    try:
        with open(CACHE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _speichere_cache(daten: Dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump(daten, fh, ensure_ascii=False, indent=1)
    except Exception:
        pass


def get_universe(force_refresh: bool = False) -> Dict[str, Any]:
    """Symbols to scan, plus an honest statement of where they came from."""
    cache = _lade_cache()
    frisch = False
    if cache and not force_refresh:
        try:
            frisch = (time.time() - float(cache.get("geholt_ts", 0))) < REFRESH_AFTER_DAYS * 86400
        except Exception:
            frisch = False
        if frisch:
            cache["herkunft"] = "zwischengespeichert"
            return cache

    symbole: List[str] = []
    quellen: Dict[str, int] = {}
    fehler: Dict[str, str] = {}
    for label, url, suffix in QUELLEN:
        try:
            liste = _hole_liste(url, suffix)
            if liste:
                symbole.extend(liste)
                quellen[label] = len(liste)
            else:
                fehler[label] = "keine Tabelle mit Ticker-Spalte gefunden"
        except Exception as e:
            fehler[label] = str(e)[:90]

    if not symbole:
        if cache:
            cache["herkunft"] = "zwischengespeichert (Abruf fehlgeschlagen)"
            cache["abruffehler"] = fehler
            return cache
        from src.universe import FULL_MARKET_UNIVERSE
        return {
            "symbole": [s for s in dict.fromkeys(FULL_MARKET_UNIVERSE)
                        if "-USD" not in s and "=" not in s],
            "quellen": {"Handelsuniversum (Notbehelf)": 0},
            "herkunft": "Notbehelf - keine Indexliste abrufbar",
            "abruffehler": fehler,
            "stand": None,
        }

    # The trading universe stays in: those names are already being watched, and
    # a candidate the depots could actually buy is worth more than one they cannot.
    from src.universe import FULL_MARKET_UNIVERSE
    handel = [s for s in FULL_MARKET_UNIVERSE if "-USD" not in s and "=" not in s]
    symbole.extend(handel)
    quellen["Handelsuniversum"] = len(handel)

    daten = {
        "symbole": sorted(dict.fromkeys(symbole)),
        "quellen": quellen,
        "abruffehler": fehler,
        "geholt_ts": time.time(),
        "stand": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "herkunft": "frisch abgerufen",
    }
    _speichere_cache(daten)
    return daten
