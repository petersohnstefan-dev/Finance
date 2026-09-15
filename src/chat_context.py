"""Assembles the live system state for the chatbot.

The chat prompt used to carry a hardcoded "HEUTE IST DER 29.08.2026", the raw
portfolios.json dump and nothing else - no tribunal verdicts, no insider or whale
activity, no news, no scan results, no trade statistics. It was also instructed
to never admit missing data, so whatever it was not given it invented.

This module gathers what the system actually knows, dates it from the clock, and
marks every section that could not be loaded as unavailable so the model can say
so instead of filling the gap.
"""
import datetime
import json
import sqlite3
from typing import Any, Dict, List, Optional

from src.paths import data_file


def _fmt_eur(v: Optional[float]) -> str:
    return "-" if v is None else f"{v:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")


def _load_json(name: str) -> Optional[Any]:
    try:
        with open(data_file(name), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


# ---------------------------------------------------------------- sections
def section_time() -> str:
    from src.market_seasonality import get_berlin_now
    now = get_berlin_now()
    weekday = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
               "Freitag", "Samstag", "Sonntag"][now.weekday()]
    return (f"## ZEITPUNKT\n"
            f"Jetzt ist {weekday}, der {now.strftime('%d.%m.%Y')}, {now.strftime('%H:%M')} Uhr "
            f"(Europe/Berlin). Rechne Zeitangaben wie 'heute' oder 'diese Woche' "
            f"immer von diesem Zeitpunkt aus.\n")


def section_depots(pm) -> str:
    out = ["## DEPOTS (Stand jetzt)"]
    labels = {"day_trading": "Daytrader", "short_term": "Kurzfrist",
              "medium_term": "Mittelfrist", "long_term": "Langfrist"}
    for key, label in labels.items():
        try:
            s = pm.get_depot_summary(key)
        except Exception as exc:
            out.append(f"\n### {label}: nicht ladbar ({type(exc).__name__})")
            continue
        ts = s.get("trade_stats", {})
        out.append(
            f"\n### {label} ({key})\n"
            f"Gesamtwert {_fmt_eur(s['total_value'])} | "
            f"Cash {_fmt_eur(s['cash'])} ({s['cash_ratio_pct']:.1f}%) | "
            f"investiert {_fmt_eur(s['invested_value'])}\n"
            f"Gesamt-P&L {s['total_pnl']:+,.2f} EUR ({s['total_pnl_pct']:+.2f}%) | "
            f"heute {s.get('today_pnl', 0):+,.2f} EUR")
        if ts.get("closed_trades"):
            pf = ts.get("profit_factor")
            pf_txt = "unendlich" if pf == float("inf") else ("-" if pf is None else f"{pf:.2f}")
            out.append(
                f"Abgeschlossene Trades: {ts['closed_trades']} "
                f"({ts['wins']} im Plus / {ts['losses']} im Minus, "
                f"Trefferquote {ts['win_rate_pct']:.1f}%). "
                f"Durchschnitt: +{ts['avg_win']:,.2f} EUR je Gewinner gegen "
                f"-{ts['avg_loss']:,.2f} EUR je Verlierer, Profit-Faktor {pf_txt}, "
                f"realisiert {ts['realized_pnl']:+,.2f} EUR.")
        else:
            out.append("Noch kein Trade abgeschlossen.")

        if s["positions"]:
            out.append("Offene Positionen:")
            for p in s["positions"]:
                out.append(
                    f"  - {p.get('name', p.get('symbol'))} ({p.get('symbol')}): "
                    f"Einstand {p.get('buy_price')}, aktuell {p.get('current_price')}, "
                    f"{p.get('pnl_pct', 0):+.1f}% | Stop {p.get('stop_loss')} | "
                    f"gekauft {p.get('buy_date', '-')} | Begruendung: "
                    f"{str(p.get('reason', ''))[:160]}")
        else:
            out.append("Keine offenen Positionen.")
    return "\n".join(out) + "\n"


def section_trades(pm, limit: int = 25) -> str:
    rows: List[str] = []
    for key in ("day_trading", "short_term", "medium_term", "long_term"):
        try:
            hist = pm.get_depot_summary(key)["history"]
        except Exception:
            continue
        for t in hist[:limit]:
            pnl = t.get("pnl")
            pnl_txt = f" | Ergebnis {float(pnl):+,.2f} EUR ({t.get('pnl_pct', 0)}%)" if pnl is not None else ""
            rows.append(
                f"- {t.get('date')} | {key} | {t.get('type')} "
                f"{t.get('name') or t.get('ticker')} ({t.get('ticker')}) | "
                f"{t.get('shares')} Stueck zu {t.get('price')}{pnl_txt} | "
                f"Begruendung: {str(t.get('reason', ''))[:220]}")
    if not rows:
        return "## TRANSAKTIONEN\nKeine Transaktionen vorhanden.\n"
    rows.sort(reverse=True)
    return ("## TRANSAKTIONEN (neueste zuerst, alle Depots)\n"
            "Jede Zeile ist ein tatsaechlich ausgefuehrter Kauf oder Verkauf mit der "
            "Begruendung, die das System dabei protokolliert hat.\n"
            + "\n".join(rows[:60]) + "\n")


def section_tribunal(limit: int = 12) -> str:
    try:
        from src.tribunal import AITribunalManager
        logs = AITribunalManager.get_latest_logs(limit)
    except Exception as exc:
        return f"## KI-TRIBUNAL\nNicht ladbar ({type(exc).__name__}).\n"
    if not logs:
        return ("## KI-TRIBUNAL\nNoch keine Verhandlung protokolliert. Das Tribunal "
                "tagt nur, wenn ein Kaufkandidat alle vorgelagerten Filter passiert hat.\n")
    out = ["## KI-TRIBUNAL (Kaufpruefungen, neueste zuerst)",
           "Vor jedem Kauf ausser im Daytrader-Depot plaedieren ein Bulle und ein Baer "
           "unabhaengig voneinander, ein dritter Aufruf entscheidet."]
    for lg in logs:
        out.append(
            f"\n- {lg.get('timestamp')} | {lg.get('symbol')} "
            f"({lg.get('name') or '-'}) | Depot {lg.get('depot_id')} | URTEIL: {lg.get('action')}"
            + (f"\n  Ausschlaggebend: {lg['decisive_factor']}" if lg.get("decisive_factor") else "")
            + f"\n  Bulle: {str(lg.get('bull_case', ''))[:300]}"
            + f"\n  Baer:  {str(lg.get('bear_case', ''))[:300]}"
            + f"\n  Richter: {str(lg.get('judge_decision', ''))[:300]}")
    return "\n".join(out) + "\n"


def section_insider_whales(max_rows: int = 15) -> str:
    out = []
    try:
        from src.insider_whale_tracker import LiveInsiderWhaleTracker as T
    except Exception:
        try:
            import src.insider_whale_tracker as m
            T = next(v for v in vars(m).values()
                     if isinstance(v, type) and hasattr(v, "get_live_insider_transactions"))
        except Exception as exc:
            return f"## INSIDER & WALE\nNicht ladbar ({type(exc).__name__}).\n"

    try:
        df = T.get_live_insider_transactions()
        if df is not None and not df.empty:
            out.append("## INSIDER-TRANSAKTIONEN (SEC Form 4 ueber yfinance, echte Daten)")
            for _, r in df.head(max_rows).iterrows():
                out.append("- " + " | ".join(f"{c}: {r[c]}" for c in df.columns if c in r))
        else:
            out.append("## INSIDER-TRANSAKTIONEN\nAktuell keine Meldungen abrufbar.")
    except Exception as exc:
        out.append(f"## INSIDER-TRANSAKTIONEN\nAbruf fehlgeschlagen ({type(exc).__name__}).")

    try:
        wdf = T.get_live_whale_holders()
        if wdf is not None and not wdf.empty:
            out.append("\n## GROSSINVESTOREN / WALE (institutionelle Halter)")
            for _, r in wdf.head(max_rows).iterrows():
                out.append("- " + " | ".join(f"{c}: {r[c]}" for c in wdf.columns if c in r))
        else:
            out.append("\n## GROSSINVESTOREN\nAktuell keine Daten abrufbar.")
    except Exception as exc:
        out.append(f"\n## GROSSINVESTOREN\nAbruf fehlgeschlagen ({type(exc).__name__}).")
    return "\n".join(out) + "\n"


def section_buzz(pm, max_symbols: int = 10) -> str:
    """News and forum activity for what the depots hold and what is being scanned."""
    symbols: List[str] = []
    try:
        for key in ("short_term", "medium_term", "long_term"):
            for sym in pm.data["portfolios"][key]["positions"]:
                pos = pm.data["portfolios"][key]["positions"][sym]
                symbols.append(pos.get("underlying_symbol", sym))
    except Exception:
        pass
    scan = _load_json("market_scan_results.json") or {}
    top = sorted(scan.get("data", []), key=lambda r: -(r.get("total_score") or 0))[:5]
    symbols += [r["symbol"] for r in top]
    seen, ordered = set(), []
    for s in symbols:
        if s not in seen:
            seen.add(s)
            ordered.append(s)

    out = ["## NACHRICHTENLAGE & SOCIAL BUZZ",
           "Nachrichten-Sentiment 0-100 (50 = neutral) aus den letzten Schlagzeilen."]
    try:
        from src.deep_intelligence import SocialSentimentEngine as S
        for sym in ordered[:max_symbols]:
            d = S.get_social_spike_score(sym)
            if not d.get("available"):
                out.append(f"- {sym}: keine Schlagzeilen abrufbar")
                continue
            heads = "; ".join(h[:90] for h in (d.get("recent_headlines") or [])[:2])
            out.append(f"- {sym}: Sentiment {d['nlp_sentiment_score']}/100 "
                       f"({d.get('alert', '')}), {d.get('headline_count')} Meldungen. {heads}")
    except Exception as exc:
        out.append(f"Nachrichten nicht ladbar ({type(exc).__name__}).")

    forum = [r for r in scan.get("data", []) if (r.get("forum_mentions") or 0) > 0]
    if forum:
        out.append("\n### Reddit-Erwaehnungen aus dem Markt-Scan")
        for r in sorted(forum, key=lambda x: -x["forum_mentions"])[:10]:
            out.append(f"- {r['symbol']}: {r['forum_mentions']} Erwaehnungen, "
                       f"Forum-Sentiment {r.get('forum_sentiment')}/100")
    else:
        out.append("\n### Reddit\nKeine Forendaten vorhanden. Der Scanner braucht dafuer "
                   "REDDIT_CLIENT_ID und REDDIT_CLIENT_SECRET; ohne diese Secrets bleibt "
                   "die Quelle inaktiv. Sag das offen, statt Foren-Aktivitaet zu erfinden.")
    return "\n".join(out) + "\n"


def section_scan(limit: int = 12) -> str:
    scan = _load_json("market_scan_results.json")
    if not scan:
        return "## MARKT-SCAN\nKeine Scan-Ergebnisse vorhanden.\n"
    rows = sorted(scan.get("data", []), key=lambda r: -(r.get("total_score") or 0))[:limit]
    out = [f"## MARKT-SCAN (Stand {scan.get('scan_time', '?')}, "
           f"{scan.get('total_scanned', len(scan.get('data', [])))} Werte geprueft)",
           "Bestbewertete Kandidaten:"]
    for r in rows:
        out.append(f"- {r['symbol']} ({r.get('name', '')[:30]}): Gesamt {r.get('total_score')}, "
                   f"kurz {r.get('short_score')}, lang {r.get('long_score')}, "
                   f"Breakout {r.get('breakout_score')}, RSI {r.get('rsi')}, "
                   f"Sektor {r.get('sector')}, {r.get('breakout_status', '')[:60]}")
    return "\n".join(out) + "\n"


def section_alerts(limit: int = 10) -> str:
    alerts = _load_json("realtime_alerts.json")
    if not alerts:
        return "## ECHTZEIT-ALARME\nKeine Alarme vorhanden.\n"
    out = ["## ECHTZEIT-ALARME (Intraday-Ausbrueche, neueste zuerst)"]
    for a in alerts[:limit]:
        out.append(f"- {a.get('time_str')} {a.get('symbol')}: {a.get('change_1min_pct')}% "
                   f"in 5 Min ({a.get('direction')}), Volumen {a.get('vol_ratio', 'o. A.')}x")
    return "\n".join(out) + "\n"


def section_strategy() -> str:
    strat = _load_json("strategy.json")
    if not strat:
        return ""
    return ("## AKTIVE STRATEGIE-PARAMETER\n"
            "Diese Werte steuern die Automatik und werden vom KI-Lerntagebuch angepasst:\n"
            + json.dumps(strat, indent=1, ensure_ascii=False) + "\n")


def section_journal(limit: int = 4) -> str:
    try:
        conn = sqlite3.connect(data_file("portfolio.db"))
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(
            "SELECT date, depot_id, mode, win_rate, reflection, lesson, param_updates "
            "FROM ai_journal ORDER BY id DESC LIMIT ?", (limit,))]
        conn.close()
    except Exception:
        return ""
    if not rows:
        return ""
    out = ["## KI-LERNTAGEBUCH (letzte Retrospektiven)"]
    for r in rows:
        out.append(f"\n- {r.get('date')} | {r.get('depot_id')} | {r.get('mode')} | "
                   f"Win-Rate {r.get('win_rate')}%\n"
                   f"  Erkenntnis: {str(r.get('lesson') or '')[:300]}\n"
                   f"  Parameteraenderungen: {r.get('param_updates')}")
    return "\n".join(out) + "\n"


def section_macro() -> str:
    parts = ["## MAKRO-DATEN (live)"]
    try:
        from src.bonds_yields_radar import BondYieldsIntelEngine as B
        b = B.get_bond_market_overview()
        parts.append(f"- US 10J-Rendite {b['us_10y_yield']:.2f}%, 2J {b['us_2y_yield']:.2f}%, "
                     f"Spread {b['spread_10y_2y_bps']:.1f} Bps ({b['curve_regime']})")
    except Exception:
        parts.append("- Anleihedaten nicht abrufbar")
    try:
        from src.commodities_forex_radar import CommoditiesIntelEngine as C, ForexCurrencyEngine as F
        pm_ov = C.get_precious_metals_overview()
        fx = F.get_forex_overview()
        parts.append(f"- Gold ${pm_ov['gold_price']:.2f}, Silber ${pm_ov['silver_price']:.2f}, "
                     f"Gold/Silber-Ratio {pm_ov['gold_silver_ratio']}")
        parts.append(f"- DXY {fx.get('dxy_index')}, USD/JPY "
                     f"{fx.get('rates', {}).get('USD/JPY')}, "
                     f"Carry-Risiko: {fx.get('jpy_carry_trade_risk')}")
    except Exception:
        parts.append("- Rohstoff-/Devisendaten nicht abrufbar")
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------- assembly
def build_context(pm=None) -> str:
    """Full system state as one text block for the chat system prompt."""
    if pm is None:
        from src.portfolio import PortfolioManager
        pm = PortfolioManager()

    blocks = [section_time()]
    for fn, label in ((section_depots, "Depots"), (section_trades, "Transaktionen"),
                      (section_tribunal, "Tribunal"), (section_scan, "Markt-Scan"),
                      (section_alerts, "Alarme"), (section_buzz, "Buzz"),
                      (section_insider_whales, "Insider"), (section_macro, "Makro"),
                      (section_strategy, "Strategie"), (section_journal, "Lerntagebuch")):
        try:
            blocks.append(fn(pm) if fn in (section_depots, section_trades, section_buzz) else fn())
        except Exception as exc:
            blocks.append(f"## {label.upper()}\nAbschnitt nicht ladbar ({type(exc).__name__}).\n")
    return "\n".join(blocks)
