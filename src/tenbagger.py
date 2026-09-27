"""Suche nach Vervielfachern - nach dem, was eine Verzehnfachung antreibt.

FOCUS MONEY's Lynch screen scores what a company HAS DONE: three-year earnings
growth, three-year revenue growth, PEG, P/E, debt, size. That is not wrong - you
can only measure a company by what it has actually delivered - but it answers the
question "was this a good business" and a tenbagger needs the answer to "can this
business keep compounding from here".

Three things separate the two questions, and none of them appear in that screen:

  1. The compounding engine. A company that earns 25% on capital AND keeps
     deploying more capital doubles its earnings power every three years without
     anything else happening. One that earns 25% on a base it cannot grow is a
     fine business and a poor tenbagger. Return on invested capital multiplied by
     how much capital is actually being put to work is the engine; growth rates
     are its exhaust.

  2. Dilution. This kills more tenbaggers than any other single factor and no
     backward growth metric sees it. A company whose earnings grow tenfold while
     its share count triples hands the shareholder a threebagger. In Lynch's era
     dilution was rare; with today's share-based compensation it is the norm.

  3. The second derivative. A three-year average deliberately throws away whether
     growth is accelerating or decaying. Those are opposite futures with identical
     three-year numbers.

Deliberately NOT in the score: valuation. A screen that rewards cheapness while
searching for tenbaggers systematically surfaces value traps - the cheap ones are
usually cheap because the compounding has stopped. P/E and the growth-adjusted
multiple are carried as DISPLAY columns so the entry price can be judged
separately from the business. That is a judgement, and it is the one place where
this scoring deviates from Lynch on purpose rather than by addition.

Every factor is scored only where the filings actually support it; missing pieces
are removed from the weighting and reported as `datenlage`, the same rule the
composite alpha score follows. A score is never filled in with a constant.
"""
from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

from src.fundamentals import (_pick, _safe_div, compute_altman_z,
                              compute_beneish_m)
from src.paths import data_file

DB_FILE = data_file("portfolio.db")
CACHE_FILE = data_file("tenbagger_cache.json")

#: A scored symbol keeps for a month. The inputs are annual filings, so this is
#: generous rather than stale, and it is what makes a weekly run affordable.
CACHE_DAYS = 30

#: Yahoo throttles hard. The first full run asked for 1,402 sizes and 380 sets of
#: statements at six threads; 982 sizes and every single statement came back
#: empty, and symbols that had worked minutes earlier stopped working. So a run
#: refreshes a slice of the universe, oldest entries first, and assembles the
#: list from the cache. Four weekly runs cover the whole field, which matches how
#: often the underlying filings change anyway.
MAX_REFRESHES_PER_RUN = 150

#: Two threads, not six. The wall-clock cost is irrelevant for a weekly job and
#: a throttled run costs a whole week.
DEFAULT_WORKERS = 2

#: Pause between two requests from the same worker.
REQUEST_PAUSE_S = 0.35

#: Scores at or above these marks earn the label. Calibrated against a 220-name
#: sample of the scan universe: median 20, 90th percentile 44, 95th 51, best 67.
#: Absolute thresholds picked from that distribution rather than from a round
#: number, so the top band stays roughly the best one percent.
BAND_TENBAGGER = 60
BAND_STRONG = 50
BAND_WATCH = 40

#: Below this much of the score being backed by real figures the candidate is
#: not listed at all - a high score computed from two factors means nothing.
MIN_DATA_QUALITY = 0.60

USD_EUR = 0.895


# ---------------------------------------------------------------------------
# Plattencache
# ---------------------------------------------------------------------------
def _cache_laden() -> Dict[str, Any]:
    try:
        with open(CACHE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _cache_speichern(cache: Dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, ensure_ascii=False)
    except Exception:
        pass


#: Reasons that mean "the request did not work", as opposed to "this company
#: legitimately cannot be scored". Only the former point at throttling, and only
#: the former may be thrown out of the cache on the suspicion of it.
_FEHLSCHLAG_GRUENDE = ("Keine Marktkapitalisierung", "Keine Abschlussdaten",
                       "Eckdaten:", "Abruf fehlgeschlagen",
                       "Zu wenige Geschäftsjahre")


def _abruf_fehlgeschlagen(grund: Optional[str]) -> bool:
    g = str(grund or "")
    return any(g.startswith(x) or x in g for x in _FEHLSCHLAG_GRUENDE)


def _alter_tage(eintrag: Dict[str, Any]) -> float:
    try:
        return (time.time() - float(eintrag.get("ts", 0))) / 86400.0
    except Exception:
        return 9999.0


# ---------------------------------------------------------------------------
# Kennzahlen aus den Abschlüssen
# ---------------------------------------------------------------------------
def _cagr_vorsichtig(df, namen, spalten: int) -> Optional[float]:
    """Growth measured from two different starting years, the lower one kept.

    A single lookback is at the mercy of what the base year happened to be. E.ON
    came out of this screen at 38% gross-profit growth a year and a motor score of
    96 - arithmetically correct and economically meaningless, because the starting
    year was the bottom of the energy crisis. Measuring from the year after as
    well, and keeping whichever reading is less flattering, removes that without
    needing a rule about which industries are allowed to appear.
    """
    neu = _pick(df, namen, 0)
    werte = []
    for basis in (spalten, spalten - 1):
        if basis < 1:
            continue
        w = _cagr(neu, _pick(df, namen, basis), float(basis))
        if w is not None:
            werte.append(w)
    return min(werte) if werte else None


def _cagr(neu: Optional[float], alt: Optional[float], jahre: float) -> Optional[float]:
    """Compound annual growth. Undefined when the base is zero or negative -
    a company that went from a loss to a profit has no meaningful growth RATE."""
    if neu is None or alt is None or alt <= 0 or jahre <= 0:
        return None
    if neu <= 0:
        return -1.0
    try:
        return (neu / alt) ** (1.0 / jahre) - 1.0
    except Exception:
        return None


def _kennzahlen(inc: pd.DataFrame, bal: pd.DataFrame,
                cf: pd.DataFrame) -> Dict[str, Optional[float]]:
    """Everything the factors need, read once from the three statements."""
    n = min(len(inc.columns) if inc is not None else 0,
            len(bal.columns) if bal is not None else 0,
            len(cf.columns) if cf is not None else 0)
    if n < 2:
        return {}
    aelteste = min(n - 1, 3)                 # up to a three-year span
    spanne = float(aelteste)

    umsatz0 = _pick(inc, ["Total Revenue", "Operating Revenue"], 0)
    umsatz1 = _pick(inc, ["Total Revenue", "Operating Revenue"], 1)
    umsatz_alt = _pick(inc, ["Total Revenue", "Operating Revenue"], aelteste)
    brutto0 = _pick(inc, ["Gross Profit"], 0)
    brutto_alt = _pick(inc, ["Gross Profit"], aelteste)
    ebit0 = _pick(inc, ["EBIT", "Operating Income", "Total Operating Income As Reported"], 0)
    steuer0 = _pick(inc, ["Tax Provision"], 0)
    vorsteuer0 = _pick(inc, ["Pretax Income"], 0)
    gewinn0 = _pick(inc, ["Net Income", "Net Income Common Stockholders"], 0)
    aktien0 = _pick(inc, ["Diluted Average Shares", "Basic Average Shares"], 0) \
        or _pick(bal, ["Ordinary Shares Number", "Share Issued"], 0)
    aktien_alt = _pick(inc, ["Diluted Average Shares", "Basic Average Shares"], aelteste) \
        or _pick(bal, ["Ordinary Shares Number", "Share Issued"], aelteste)

    schulden0 = _pick(bal, ["Total Debt"], 0) or 0.0
    eigenkap0 = _pick(bal, ["Stockholders Equity", "Common Stock Equity",
                            "Total Equity Gross Minority Interest"], 0)
    eigenkap_alt = _pick(bal, ["Stockholders Equity", "Common Stock Equity",
                               "Total Equity Gross Minority Interest"], aelteste)
    kasse0 = _pick(bal, ["Cash And Cash Equivalents",
                         "Cash Cash Equivalents And Short Term Investments"], 0) or 0.0
    schulden_alt = _pick(bal, ["Total Debt"], aelteste) or 0.0
    kasse_alt = _pick(bal, ["Cash And Cash Equivalents",
                            "Cash Cash Equivalents And Short Term Investments"], aelteste) or 0.0

    ocf0 = _pick(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], 0)
    fcf_summe = 0.0
    gewinn_summe = 0.0
    fcf_jahre = 0
    for i in range(0, aelteste + 1):
        f = _pick(cf, ["Free Cash Flow"], i)
        g = _pick(inc, ["Net Income", "Net Income Common Stockholders"], i)
        if f is not None and g is not None:
            fcf_summe += f
            gewinn_summe += g
            fcf_jahre += 1

    # Invested capital: what the business actually runs on. Measured from two
    # starting years like the growth rates, for the same reason - a crisis year
    # as the base makes any recovery look like compounding.
    def ic_jahr(i):
        sch = _pick(bal, ["Total Debt"], i) or 0.0
        ek = _pick(bal, ["Stockholders Equity", "Common Stock Equity",
                         "Total Equity Gross Minority Interest"], i)
        ka = _pick(bal, ["Cash And Cash Equivalents",
                         "Cash Cash Equivalents And Short Term Investments"], i) or 0.0
        wert = sch + (ek or 0.0) - ka
        return wert or None

    ic0 = ic_jahr(0)
    ic_cagr_werte = []
    for basis in (aelteste, aelteste - 1):
        if basis < 1:
            continue
        w = _cagr(ic0, ic_jahr(basis), float(basis))
        if w is not None:
            ic_cagr_werte.append(w)
    ic_cagr = min(ic_cagr_werte) if ic_cagr_werte else None

    steuersatz = _safe_div(steuer0, vorsteuer0)
    if steuersatz is None or not (0.0 <= steuersatz <= 0.6):
        steuersatz = 0.25                    # plausible default, never a made-up result

    # NOPAT averaged over the available years rather than taken from the latest
    # one. A single year hands the screen whatever that year happened to be:
    # E.ON's 2025 operating profit put its return on capital at 24%, which is a
    # statement about the energy crisis and not about the business.
    ebits = [_pick(inc, ["EBIT", "Operating Income",
                         "Total Operating Income As Reported"], i)
             for i in range(0, aelteste + 1)]
    ebits = [e for e in ebits if e is not None]
    nopat = (sum(ebits) / len(ebits)) * (1.0 - steuersatz) if ebits else None
    nopat_letztes = (ebits[0] * (1.0 - steuersatz)) if ebits else None

    return {
        "jahresspanne": spanne,
        "umsatz_cagr": _cagr_vorsichtig(inc, ["Total Revenue", "Operating Revenue"], aelteste),
        "umsatz_letztes_jahr": _cagr(umsatz0, umsatz1, 1.0),
        "umsatz_vorletztes_jahr": _cagr(
            umsatz1, _pick(inc, ["Total Revenue", "Operating Revenue"], 2), 1.0),
        "brutto_cagr": _cagr_vorsichtig(inc, ["Gross Profit"], aelteste),
        "bruttomarge_jetzt": _safe_div(brutto0, umsatz0),
        "bruttomarge_frueher": _safe_div(brutto_alt, umsatz_alt),
        "roic": _safe_div(nopat, ic0),
        "roic_letztes": _safe_div(nopat_letztes, ic0),
        "ic_cagr": ic_cagr,
        "aktien_cagr": _cagr(aktien0, aktien_alt, spanne),
        "nettoschuld": (schulden0 - kasse0),
        "ocf": ocf0,
        "kasse": kasse0,
        "fcf_deckung": _safe_div(fcf_summe, gewinn_summe) if fcf_jahre >= 2 and gewinn_summe > 0 else None,
        "fcf_letztes": _pick(cf, ["Free Cash Flow"], 0),
        "gewinn": gewinn0,
        "umsatz": umsatz0,
    }


# ---------------------------------------------------------------------------
# Die sechs Geschaeftsfaktoren plus der Groessenfaktor
# ---------------------------------------------------------------------------
def _stufe(wert: Optional[float], stufen: List[Tuple[float, float]],
           unterste: float) -> Optional[float]:
    """First threshold the value clears, walking from the top down."""
    if wert is None:
        return None
    for grenze, punkte in stufen:
        if wert >= grenze:
            return punkte
    return unterste


#: Room to grow is not one factor among several - it is the arithmetic ceiling
#: on the whole question, so it multiplies the business score instead of adding
#: to it. Nvidia scores 86 of 100 on business quality and deserves to; at 4,864
#: billion euros a tenfold rise would mean a 49 trillion company, more than the
#: world produces in a year. As a summand that impossibility cost 15 points and
#: still left a "strong candidate". As a multiplier it settles the question.
SIZE_MULTIPLIER = [
    (5.0, 1.00),        # up to 5 bn: a tenbagger is entirely ordinary
    (10.0, 0.92),
    (25.0, 0.80),
    (50.0, 0.62),
    (100.0, 0.40),
    (250.0, 0.22),
]
SIZE_MULTIPLIER_ABOVE = 0.10


def groessenfaktor(marktkap_eur: Optional[float]) -> Optional[float]:
    """Multiplier between 0.10 and 1.00 from market capitalisation."""
    if not marktkap_eur or marktkap_eur <= 0:
        return None
    mrd = marktkap_eur / 1e9
    for grenze, faktor in SIZE_MULTIPLIER:
        if mrd <= grenze:
            return faktor
    return SIZE_MULTIPLIER_ABOVE


def _wachstumsmotor(k: Dict[str, Optional[float]]) -> Dict[str, Any]:
    """The four factors that actually PRODUCE a tenfold rise, 100 points.

    An earlier version scored growth and prudence side by side and E.ON came out
    at 85 of 100, ahead of every fast grower in the sample. That was the model
    telling the truth about itself: dilution, survivability and cash conversion
    made up 35 of 85 points, and a mature utility wins all three by never trying
    anything. A company that does not grow cannot be a tenbagger no matter how
    carefully it is run, so prudence was moved out of the score entirely - see
    _abzuege, where it can only ever subtract.
    """
    f: Dict[str, Any] = {}

    # 1. Kapitalverzinsung. What each euro put into the business earns back.
    roic = k.get("roic")
    # Averaged over the available years on purpose, but a company that only
    # turned the corner recently is handicapped by that average and deserves to
    # be told apart from one that is fading - so both readings are reported.
    roic_neu = k.get("roic_letztes")
    if roic is not None and roic_neu is not None and abs(roic_neu - roic) > 0.05:
        hinweis = (f"letztes Jahr {roic_neu*100:.1f}% - "
                   + ("erst kuerzlich erreicht" if roic_neu > roic else "rueckläufig"))
    else:
        hinweis = None
    f["kapitalverzinsung"] = {
        "max": 25,
        "punkte": _stufe(roic, [(0.30, 25), (0.22, 21), (0.15, 16),
                                (0.10, 11), (0.05, 5)], 0),
        "wert": (round(roic * 100, 1) if roic is not None else None),
        "einheit": "% Rendite auf eingesetztes Kapital (Mehrjahresschnitt)",
        "zusatz": hinweis,
    }

    # 2. Wachstumsqualitaet. Gross profit, not revenue: revenue can be bought
    #    with discounts, gross profit cannot. The margin trend says whether
    #    scale is turning into pricing power.
    bg = k.get("brutto_cagr")
    m_jetzt, m_frueher = k.get("bruttomarge_jetzt"), k.get("bruttomarge_frueher")
    delta_marge = ((m_jetzt - m_frueher) * 100.0
                   if m_jetzt is not None and m_frueher is not None else None)
    p_bg = _stufe(bg, [(0.35, 22), (0.25, 18), (0.15, 13), (0.08, 7), (0.03, 3)], 0)
    p_marge = _stufe(delta_marge, [(3.0, 8), (0.0, 5), (-2.0, 2)], 0)
    f["wachstumsqualitaet"] = {
        "max": 30,
        "punkte": (None if p_bg is None and p_marge is None
                   else (p_bg or 0) + (p_marge or 0)),
        "wert": (round(bg * 100, 1) if bg is not None else None),
        "einheit": "% Bruttogewinn pro Jahr",
        "zusatz": (f"Bruttomarge {delta_marge:+.1f} Prozentpunkte"
                   if delta_marge is not None else None),
    }

    # 3. Beschleunigung. The figure a three-year average is built to hide: two
    #    companies with the same three-year growth, one speeding up and one
    #    running out, are opposite futures with identical statistics.
    # Two consecutive annual growth rates, not this year against a multi-year
    # average: the average moves when the lookback changes, and a more
    # conservative average would inflate the apparent acceleration for free.
    letztes, vorletztes = k.get("umsatz_letztes_jahr"), k.get("umsatz_vorletztes_jahr")
    beschl = ((letztes - vorletztes) * 100.0
              if letztes is not None and vorletztes is not None else None)
    punkte = _stufe(beschl, [(8.0, 20), (2.0, 15), (-2.0, 9), (-8.0, 4)], 0)
    # A company slowing from 120% to 60% a year reads as a 60-point deceleration
    # and scored zero here, which is absurd: it is still growing faster than
    # almost anything else in the market. Below full speed the deceleration
    # matters; at high absolute growth it does not yet.
    gebremst_aber_schnell = (punkte is not None and letztes is not None
                             and letztes >= 0.25 and punkte < 9)
    if gebremst_aber_schnell:
        punkte = 9
    f["beschleunigung"] = {
        "max": 20,
        "punkte": punkte,
        "wert": (round(beschl, 1) if beschl is not None else None),
        "einheit": "Prozentpunkte Wachstum letztes ggü. vorletztem Jahr",
        "zusatz": ("Verlangsamung nicht gewertet - Wachstum liegt weiterhin über 25%"
                   if gebremst_aber_schnell else None),
    }

    # 4. Reinvestition. A high return on a base that cannot grow compounds
    #    nothing - and growth bought at a return below the cost of capital
    #    destroys value rather than creating it. So the points for deploying
    #    capital are scaled by what that capital earns: a regulated utility
    #    growing its asset base 20% a year at allowed returns is not compounding
    #    anything for a shareholder, and used to collect full marks here.
    ic = k.get("ic_cagr")
    roh = _stufe(ic, [(0.20, 25), (0.12, 20), (0.06, 14), (0.02, 8)], 3)
    guete = (None if roic is None else
             1.00 if roic >= 0.20 else
             0.85 if roic >= 0.15 else
             0.60 if roic >= 0.10 else
             0.30 if roic >= 0.05 else 0.0)
    f["reinvestition"] = {
        "max": 25,
        "punkte": (None if roh is None else
                   round(roh * (guete if guete is not None else 0.6))),
        "wert": (round(ic * 100, 1) if ic is not None else None),
        "einheit": "% eingesetztes Kapital pro Jahr",
        "zusatz": (f"gewichtet mit der Kapitalverzinsung (Faktor {guete:.2f})"
                   if guete is not None else "Verzinsung unbekannt, Faktor 0.60"),
    }
    return f


def _abzuege(k: Dict[str, Optional[float]]) -> Dict[str, Any]:
    """The three ways a tenfold rise fails to reach the shareholder.

    These are multipliers, never points. None of them can make a company a
    candidate; each of them can take the candidacy away.
    """
    a: Dict[str, Any] = {}

    # Verwaesserung: earnings times ten with a share count times three is a
    # threebagger. At 10% a year the count is 2.6x after a decade, so the
    # company must become 26 times larger for the holder to see a tenfold rise.
    akt = k.get("aktien_cagr")
    pct = (akt * 100.0) if akt is not None else None
    a["verwaesserung"] = {
        "faktor": (1.00 if pct is None else
                   1.00 if pct <= 0 else
                   0.95 if pct <= 2 else
                   0.85 if pct <= 5 else
                   0.70 if pct <= 10 else 0.55),
        "wert": (round(pct, 1) if pct is not None else None),
        "einheit": "% Aktienzahl pro Jahr",
    }

    # Ueberlebensfaehigkeit: a company forced to raise money in a downturn
    # dilutes at the worst possible price, which feeds straight back above.
    nd, ocf = k.get("nettoschuld"), k.get("ocf")
    if ocf is not None and ocf > 0:
        verh = (nd / ocf) if nd is not None else None
        faktor = (1.00 if (nd is not None and nd <= 0) else
                  1.00 if verh is not None and verh <= 1.5 else
                  0.92 if verh is not None and verh <= 3.0 else
                  0.80 if verh is not None and verh <= 5.0 else 0.60)
        wert, einheit = ((round(verh, 2) if verh is not None else None),
                         "x Nettoschuld / operativer Cashflow")
    else:
        fcf, kasse = k.get("fcf_letztes"), k.get("kasse")
        reichweite = (kasse / abs(fcf)) if (fcf is not None and fcf < 0 and kasse) else None
        faktor = (0.75 if reichweite is None else
                  1.00 if reichweite >= 4 else
                  0.90 if reichweite >= 2.5 else
                  0.75 if reichweite >= 1.5 else 0.55)
        wert, einheit = ((round(reichweite, 1) if reichweite is not None else None),
                         "Jahre Reichweite der Barmittel (kein operativer Cashflow)")
    a["ueberlebensfaehigkeit"] = {"faktor": faktor, "wert": wert, "einheit": einheit}

    # Barmittel-Deckung: does the reported growth arrive as cash? Deliberately
    # the mildest of the three - a company growing 80% a year while building
    # inventory burns cash for good reasons, and punishing that hard would
    # remove exactly the candidates this list exists to find.
    d = k.get("fcf_deckung")
    a["barmittel_deckung"] = {
        "faktor": (1.00 if d is None else
                   1.00 if d >= 0.5 else
                   0.93 if d >= 0.2 else
                   0.88 if d >= 0 else 0.82),
        "wert": (round(d, 2) if d is not None else None),
        "einheit": "x freier Cashflow / Nettogewinn (Summe 3 Jahre)",
    }
    return a



def eckdaten(symbol: str) -> Dict[str, Any]:
    """Market cap, price and currency from the cheap endpoint.

    fast_info is one request against a small payload, .info is a large one that
    yfinance throttles. Fetching the size first lets the scan drop every name it
    cannot use before spending three statement requests on it - a fifth of the
    trading universe has no market capitalisation at all (delisted tickers,
    renamed listings) and used to cost four requests each to discover that.
    """
    def feld(fi, name):
        # FastInfo.keys() only lists the camelCase spellings, so .get("market_cap")
        # quietly returns None while fi["market_cap"] resolves. Index access it is.
        try:
            return fi[name]
        except Exception:
            return None

    try:
        fi = yf.Ticker(symbol).fast_info
        marktkap = feld(fi, "marketCap")
        waehrung = feld(fi, "currency") or "USD"
        kurs = feld(fi, "lastPrice")
    except Exception as e:
        return {"symbol": symbol, "available": False, "reason": f"Eckdaten: {str(e)[:60]}"}
    if not marktkap:
        return {"symbol": symbol, "available": False, "reason": "Keine Marktkapitalisierung"}
    waehrung = str(waehrung).upper()
    return {
        "symbol": symbol, "available": True,
        "marktkap_eur": float(marktkap) * (1.0 if waehrung == "EUR" else USD_EUR),
        "kurs": (float(kurs) if kurs else None),
        "waehrung": waehrung,
    }


def score_symbol(symbol: str, name: Optional[str] = None,
                 vorab: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Tenbagger score for one company, 0-100, with every factor itemised.

    `vorab` carries what eckdaten() already established, so a two-stage scan does
    not pay for the same figures twice.
    """
    if "-USD" in symbol or "=" in symbol:
        return {"symbol": symbol, "available": False,
                "reason": "Kein bilanzierendes Unternehmen"}
    try:
        t = yf.Ticker(symbol)
        inc, bal, cf = t.income_stmt, t.balance_sheet, t.cashflow
        if inc is None or inc.empty:
            return {"symbol": symbol, "available": False,
                    "reason": "Keine Abschlussdaten"}
        if vorab and vorab.get("available"):
            marktkap_eur = vorab.get("marktkap_eur")
            waehrung = vorab.get("waehrung", "USD")
            kurs = vorab.get("kurs")
            marktkap = (marktkap_eur / (1.0 if waehrung == "EUR" else USD_EUR)
                        if marktkap_eur else None)
            anzeige_name = name or symbol
        else:
            info = {}
            try:
                info = t.info or {}
            except Exception:
                info = {}
            marktkap = info.get("marketCap")
            waehrung = (info.get("currency") or "USD").upper()
            marktkap_eur = (float(marktkap) * (1.0 if waehrung == "EUR" else USD_EUR)
                            if marktkap else None)
            kurs = info.get("currentPrice") or info.get("regularMarketPrice")
            anzeige_name = name or info.get("shortName") or info.get("longName") or symbol
    except Exception as e:
        return {"symbol": symbol, "available": False, "reason": f"Abruf fehlgeschlagen: {e}"}

    k = _kennzahlen(inc, bal, cf)
    if not k:
        return {"symbol": symbol, "available": False,
                "reason": "Zu wenige Geschäftsjahre in den Abschlüssen"}

    motor = _wachstumsmotor(k)
    abzuege = _abzuege(k)

    # Weight only over what was actually measured, exactly like the alpha score.
    erreicht = moeglich = 0.0
    fehlend: List[str] = []
    for schluessel, d in motor.items():
        if d.get("punkte") is None:
            fehlend.append(schluessel)
            continue
        erreicht += float(d["punkte"])
        moeglich += float(d["max"])
    if moeglich <= 0:
        return {"symbol": symbol, "available": False, "reason": "Kein Faktor messbar"}

    datenlage = moeglich / 100.0
    motorscore = round(erreicht / moeglich * 100.0)
    groesse = groessenfaktor(marktkap_eur)
    if groesse is None:
        return {"symbol": symbol, "available": False,
                "reason": "Keine Marktkapitalisierung - Groesse nicht bewertbar"}
    abzugsfaktor = 1.0
    for d in abzuege.values():
        abzugsfaktor *= float(d["faktor"])
    score = round(motorscore * groesse * abzugsfaktor)

    # Valuation is reported, never scored - see the module docstring.
    kgv = None
    if k.get("gewinn") and marktkap and k["gewinn"] > 0:
        kgv = round(float(marktkap) / k["gewinn"], 1)
    wachstums_kgv = None
    if kgv and k.get("umsatz_cagr") and k["umsatz_cagr"] > 0:
        wachstums_kgv = round(kgv / (k["umsatz_cagr"] * 100.0), 2)

    # Beneish and Altman are computed from the statements already in hand.
    # Routing this through get_fundamental_scores() would fetch the same three
    # filings a second time - and it was that doubling, at six threads across
    # 1,400 symbols, that got the first full run throttled into returning
    # nothing at all.
    warnungen: List[str] = []
    try:
        m, _ = compute_beneish_m(inc, bal, cf)
        if m is not None and m > -1.78:
            warnungen.append(f"Beneish M-Score {m:.2f} - Bilanzauffälligkeit möglich")
    except Exception:
        pass
    try:
        z, _ = compute_altman_z(inc, bal, marktkap)
        if z is not None and z < 1.8:
            warnungen.append(f"Altman Z-Score {z:.2f} - Krisenbereich")
    except Exception:
        pass
    if k.get("aktien_cagr") is not None and k["aktien_cagr"] > 0.10:
        warnungen.append("Aktienzahl waechst über 10% pro Jahr")

    return {
        "symbol": symbol,
        "name": str(anzeige_name)[:40],
        "available": True,
        "score": score,
        "motorscore": motorscore,
        "groessenfaktor": groesse,
        "abzugsfaktor": round(abzugsfaktor, 3),
        "datenlage": round(datenlage, 2),
        "band": ("Tenbagger-Kandidat" if score >= BAND_TENBAGGER else
                 "Starker Kandidat" if score >= BAND_STRONG else
                 "Beobachten" if score >= BAND_WATCH else "Unauffaellig"),
        "motor": motor,
        "abzuege": abzuege,
        "fehlende_faktoren": fehlend,
        "marktkap_mrd_eur": (round(marktkap_eur / 1e9, 2) if marktkap_eur else None),
        "kurs": (round(float(kurs), 2) if kurs else None),
        "waehrung": waehrung,
        "kgv": kgv,
        "kgv_je_wachstum": wachstums_kgv,
        "warnungen": warnungen,
    }


# ---------------------------------------------------------------------------
# Historie
# ---------------------------------------------------------------------------
def ensure_tables() -> None:
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tenbagger_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT,
            score INTEGER,
            datenlage REAL,
            band TEXT,
            rang INTEGER,
            kurs REAL,
            waehrung TEXT,
            marktkap_mrd_eur REAL,
            kgv REAL,
            motorscore INTEGER,
            groessenfaktor REAL,
            abzugsfaktor REAL,
            motor TEXT,
            abzuege TEXT,
            warnungen TEXT,
            UNIQUE(scan_date, symbol)
        )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tb_symbol ON tenbagger_history(symbol)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tb_date ON tenbagger_history(scan_date)")
    conn.commit()
    conn.close()


def save_scan(rows: List[Dict[str, Any]], scan_date: Optional[str] = None) -> int:
    """Persist one scan. Re-running on the same day replaces that day's rows."""
    ensure_tables()
    tag = scan_date or datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM tenbagger_history WHERE scan_date = ?", (tag,))
    for rang, r in enumerate(rows, start=1):
        conn.execute(
            "INSERT INTO tenbagger_history (scan_date, symbol, name, score, datenlage, "
            "band, rang, kurs, waehrung, marktkap_mrd_eur, kgv, motorscore, "
            "groessenfaktor, abzugsfaktor, motor, abzuege, warnungen) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (tag, r["symbol"], r.get("name"), r.get("score"), r.get("datenlage"),
             r.get("band"), rang, r.get("kurs"), r.get("waehrung"),
             r.get("marktkap_mrd_eur"), r.get("kgv"), r.get("motorscore"),
             r.get("groessenfaktor"), r.get("abzugsfaktor"),
             json.dumps(r.get("motor"), ensure_ascii=False),
             json.dumps(r.get("abzuege"), ensure_ascii=False),
             json.dumps(r.get("warnungen"), ensure_ascii=False)))
    conn.commit()
    conn.close()
    return len(rows)


def get_scan(scan_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """One scan's list; the most recent one when no date is given."""
    ensure_tables()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    if scan_date is None:
        row = conn.execute("SELECT MAX(scan_date) FROM tenbagger_history").fetchone()
        scan_date = row[0] if row else None
    if not scan_date:
        conn.close()
        return []
    rows = conn.execute("SELECT * FROM tenbagger_history WHERE scan_date = ? "
                        "ORDER BY rang", (scan_date,)).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        for feld in ("motor", "abzuege", "warnungen"):
            try:
                d[feld] = json.loads(d[feld]) if d[feld] else None
            except Exception:
                d[feld] = None
        out.append(d)
    return out


def get_scan_dates() -> List[str]:
    ensure_tables()
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute("SELECT DISTINCT scan_date FROM tenbagger_history "
                        "ORDER BY scan_date DESC").fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_symbol_history(symbol: str) -> Dict[str, Any]:
    """How often a name appeared, since when, and what it did in the meantime."""
    ensure_tables()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT scan_date, score, rang, kurs, band FROM tenbagger_history "
                        "WHERE symbol = ? ORDER BY scan_date", (symbol,)).fetchall()
    alle_tage = conn.execute("SELECT DISTINCT scan_date FROM tenbagger_history "
                             "ORDER BY scan_date").fetchall()
    conn.close()
    if not rows:
        return {"symbol": symbol, "auftritte": 0}

    tage = [r[0] for r in alle_tage]
    eigene = [r["scan_date"] for r in rows]
    erster, letzter = rows[0], rows[-1]

    # Consecutive presence, counted from the most recent scan backwards.
    serie = 0
    for tag in reversed(tage):
        if tag in eigene:
            serie += 1
        else:
            break

    entwicklung = None
    if erster["kurs"] and letzter["kurs"]:
        entwicklung = round((letzter["kurs"] / erster["kurs"] - 1.0) * 100.0, 2)

    return {
        "symbol": symbol,
        "auftritte": len(rows),
        "von_scans": len(tage),
        "erstmals": erster["scan_date"],
        "zuletzt": letzter["scan_date"],
        "serie": serie,
        "score_erstmals": erster["score"],
        "score_aktuell": letzter["score"],
        "score_differenz": (letzter["score"] - erster["score"]
                            if erster["score"] is not None and letzter["score"] is not None
                            else None),
        "kurs_erstmals": erster["kurs"],
        "kurs_aktuell": letzter["kurs"],
        "kursentwicklung_pct": entwicklung,
        "verlauf": [{"datum": r["scan_date"], "score": r["score"],
                     "rang": r["rang"], "kurs": r["kurs"]} for r in rows],
    }


def get_watchlist() -> List[Dict[str, Any]]:
    """Every name ever listed, with its history - including those that dropped off."""
    ensure_tables()
    conn = sqlite3.connect(DB_FILE)
    symbole = [r[0] for r in conn.execute(
        "SELECT DISTINCT symbol FROM tenbagger_history").fetchall()]
    conn.close()
    aktuell = {r["symbol"] for r in get_scan()}
    out = []
    for s in symbole:
        h = get_symbol_history(s)
        h["aktuell_gelistet"] = s in aktuell
        out.append(h)
    out.sort(key=lambda h: (h["aktuell_gelistet"], h["auftritte"]), reverse=True)
    return out


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------
#: Above this the size multiplier alone makes a listing practically impossible,
#: so the statements are never fetched. A perfect motor of 100 at 100 billion
#: still only reaches 40 points.
MAX_MARKTKAP_MRD = 100.0


def run_scan(symbole: Optional[List[str]] = None,
             max_workers: int = DEFAULT_WORKERS,
             min_score: int = BAND_WATCH,
             budget: int = MAX_REFRESHES_PER_RUN,
             fortschritt: bool = True) -> Dict[str, Any]:
    """Refresh a slice of the universe and build the list from the cache.

    The list is assembled from every symbol that has ever been scored, not only
    from the ones refreshed in this run - otherwise the first weeks would show a
    quarter of the field and call it a ranking.
    """
    from concurrent.futures import ThreadPoolExecutor

    if symbole is None:
        from src.tenbagger_universe import get_universe
        uni = get_universe()
        kandidaten = uni["symbole"]
        herkunft = uni
    else:
        kandidaten = list(dict.fromkeys(symbole))
        herkunft = {"herkunft": "vorgegeben", "quellen": {"uebergeben": len(kandidaten)}}

    cache = _cache_laden()

    # Oldest first, never-scored before that. A symbol whose entry is still
    # fresh is skipped entirely - no request, no throttling risk.
    def dringlichkeit(sym: str) -> float:
        e = cache.get(sym)
        return 1e9 if not e else _alter_tage(e)

    faellig = [s for s in kandidaten
               if s not in cache or _alter_tage(cache[s]) >= CACHE_DAYS]
    faellig.sort(key=dringlichkeit, reverse=True)
    zu_holen = faellig[:budget]

    if fortschritt:
        print(f"  Universum {len(kandidaten)}, im Cache {len(cache)}, "
              f"fällig {len(faellig)} -> dieser Lauf holt {len(zu_holen)}", flush=True)

    neu_geholt = gedrosselt = 0

    def hole(sym: str) -> Dict[str, Any]:
        time.sleep(REQUEST_PAUSE_S)
        e = eckdaten(sym)
        if not e.get("available"):
            return {"symbol": sym, "available": False, "reason": e.get("reason")}
        if e["marktkap_eur"] / 1e9 > MAX_MARKTKAP_MRD:
            return {"symbol": sym, "available": False,
                    "reason": f"über {MAX_MARKTKAP_MRD:.0f} Mrd - keine Verzehnfachung möglich"}
        time.sleep(REQUEST_PAUSE_S)
        return score_symbol(sym, vorab=e)

    if zu_holen:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for i, r in enumerate(pool.map(hole, zu_holen), start=1):
                if fortschritt and i % 50 == 0:
                    print(f"    {i}/{len(zu_holen)} geholt", flush=True)
                cache[r["symbol"]] = {"ts": time.time(), "ergebnis": r}
                if r.get("available"):
                    neu_geholt += 1
                elif _abruf_fehlgeschlagen(r.get("reason")):
                    gedrosselt += 1
        _cache_speichern(cache)

    # Eine Drosselung sieht aus wie ein Unternehmen ohne Abschluss. Wenn fast
    # alles fehlschlaegt, war es die Drosselung - und der Cache behaelt die
    # alten Werte, statt sie durch Fehlschlaege zu ersetzen.
    if zu_holen and gedrosselt > len(zu_holen) * 0.6:
        for sym in zu_holen:
            e = cache.get(sym)
            r = (e or {}).get("ergebnis") or {}
            if e and not r.get("available") and _abruf_fehlgeschlagen(r.get("reason")):
                cache.pop(sym, None)
        _cache_speichern(cache)
        if fortschritt:
            print(f"  ACHTUNG: {gedrosselt} von {len(zu_holen)} Abrufen leer - "
                  f"vermutlich gedrosselt. Fehlschläge nicht in den Cache übernommen.",
                  flush=True)

    treffer: List[Dict[str, Any]] = []
    duenne_daten = zu_gross = ohne_daten = 0
    for sym in kandidaten:
        e = cache.get(sym)
        if not e:
            continue
        r = dict(e.get("ergebnis") or {})
        if not r.get("available"):
            if "Verzehnfachung" in str(r.get("reason", "")):
                zu_gross += 1
            else:
                ohne_daten += 1
            continue
        if r["datenlage"] < MIN_DATA_QUALITY:
            duenne_daten += 1
            continue
        if r["score"] >= min_score:
            r["cache_alter_tage"] = round(_alter_tage(e), 1)
            treffer.append(r)

    treffer.sort(key=lambda r: (r["score"], r["datenlage"]), reverse=True)

    # Company names come from the expensive endpoint, so they are fetched only
    # for names that made the list and are cached with the entry.
    fehlende_namen = [r["symbol"] for r in treffer
                      if not r.get("name") or r["name"] == r["symbol"]]
    if fehlende_namen:
        if fortschritt:
            print(f"  Namen für {len(fehlende_namen)} Werte nachladen ...", flush=True)

        def name_von(sym: str) -> tuple:
            time.sleep(REQUEST_PAUSE_S)
            try:
                info = yf.Ticker(sym).info or {}
                return sym, (info.get("shortName") or info.get("longName") or sym)
            except Exception:
                return sym, sym

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            namen = dict(pool.map(name_von, fehlende_namen))
        for r in treffer:
            if r["symbol"] in namen:
                r["name"] = str(namen[r["symbol"]])[:40]
                if r["symbol"] in cache:
                    cache[r["symbol"]]["ergebnis"]["name"] = r["name"]
        _cache_speichern(cache)

    if fortschritt:
        print(f"  fertig: {len(treffer)} gelistet aus {len(cache)} zwischengespeicherten "
              f"Bewertungen", flush=True)
    return {
        "treffer": treffer,
        "universum": herkunft,
        "geprueft": len(kandidaten),
        "im_cache": len(cache),
        "faellig": len(faellig),
        "neu_geholt": neu_geholt,
        "leer_abgerufen": gedrosselt,
        "zu_gross": zu_gross,
        "ohne_daten": ohne_daten,
        "duenne_daten": duenne_daten,
    }
