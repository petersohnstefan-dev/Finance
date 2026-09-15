"""AI Tribunal: an adversarial review before capital is committed.

Three separate calls, not one. The previous implementation asked a single model
to emit bull_case, bear_case and the verdict in one JSON object - so it wrote
both sides while already knowing where it was going. Over twelve days it
approved 10 of 10 candidates and rejected none.

Now the advocate and the sceptic run in parallel, neither aware of the other or
of any verdict, and a third call judges the two pleadings. Each side is given
the measured evidence the system actually computed (Piotroski, Altman, Beneish,
news sentiment, alpha decomposition, data coverage, stop distance, portfolio
context) rather than only the scanner's headline string - the old prompt passed
so little that the model argued from its own recollection of the ticker, and the
logs show it reasoning at length about a "Dark Pool" figure that was a modulo
artefact.
"""
import os
import json
import sqlite3
import datetime
import concurrent.futures
from zoneinfo import ZoneInfo
from typing import Dict, Any, Tuple, Optional

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

from src.paths import data_file

DB_FILE = data_file("portfolio.db")
def get_berlin_now() -> datetime.datetime:
    try:
        return datetime.datetime.now(ZoneInfo("Europe/Berlin"))
    except Exception:
        return datetime.datetime.utcnow() + datetime.timedelta(hours=2)


class AITribunalManager:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

        # Try streamlit secrets as fallback
        if not self.api_key:
            try:
                import streamlit as st
                self.api_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                pass

        if self.api_key and GENAI_AVAILABLE:
            genai.configure(api_key=self.api_key)
        elif self.api_key and not GENAI_AVAILABLE:
            # Key present but the SDK missing would otherwise crash the constructor
            # and take the whole PortfolioManager down with it.
            print("[tribunal] google-generativeai nicht installiert - Tribunal inaktiv")
            self.api_key = None

        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tribunal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                depot_id TEXT NOT NULL,
                bull_case TEXT,
                bear_case TEXT,
                judge_decision TEXT,
                action TEXT
            )
        ''')
        # Columns added after the table first shipped
        existing = {r[1] for r in cursor.execute("PRAGMA table_info(tribunal_logs)")}
        for col in ("name", "decisive_factor", "evidence"):
            if col not in existing:
                cursor.execute(f"ALTER TABLE tribunal_logs ADD COLUMN {col} TEXT")
        conn.commit()
        conn.close()

    def _get_fastest_model_name(self) -> str:
        if not hasattr(self, "_cached_model"):
            try:
                available = [m.name for m in genai.list_models()
                             if 'generateContent' in m.supported_generation_methods]
                if available:
                    # Prefer 1.5 flash specifically because it has 1500 RPM limit on free tier,
                    # whereas 2.5 flash often has a strict 20 RPM limit.
                    flash_15_models = [m for m in available if '1.5-flash' in m.lower()]
                    flash_models = [m for m in available if 'flash' in m.lower()]
                    if flash_15_models:
                        self._cached_model = flash_15_models[0]
                    elif flash_models:
                        self._cached_model = flash_models[0]
                    else:
                        self._cached_model = available[0]
                else:
                    self._cached_model = "gemini-1.5-flash"
            except Exception:
                self._cached_model = "gemini-1.5-flash"
        return self._cached_model

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------
    @staticmethod
    def build_evidence(candidate: Dict[str, Any], intel: Optional[Dict[str, Any]],
                       depot_id: str, depot: Dict[str, Any],
                       scan_row: Optional[Dict[str, Any]] = None,
                       stop_loss: Optional[float] = None) -> Dict[str, Any]:
        """Collects what the system actually measured about this candidate.

        Anything unavailable is reported as such, never filled with a placeholder,
        so neither advocate can argue from a number nobody computed.
        """
        price = candidate.get("price") or 0.0
        ev: Dict[str, Any] = {
            "symbol": candidate.get("symbol"),
            "name": candidate.get("name"),
            "depot": depot_id,
            "preis": round(price, 2) if price else None,
            "scanner_signal": candidate.get("reason", "")[:200],
        }

        if intel:
            forensic = intel.get("forensic_quality") or {}
            social = intel.get("social_sentiment") or {}
            flow = intel.get("smart_money_flow") or {}
            ev["alpha_score"] = intel.get("composite_alpha_score")
            ev["datenabdeckung_pct"] = round((intel.get("data_quality") or 0) * 100)
            ev["fehlende_bausteine"] = intel.get("data_missing") or []
            ev["piotroski"] = forensic.get("piotroski_f_score")
            ev["altman_z"] = forensic.get("altman_z_score")
            ev["beneish_m"] = forensic.get("beneish_m_score")
            ev["bilanz_rating"] = forensic.get("moat_rating")
            ev["news_sentiment"] = social.get("nlp_sentiment_score")
            ev["news_schlagzeilen"] = (social.get("recent_headlines") or [])[:3]
            ev["put_call_ratio"] = flow.get("put_call_ratio")

        if scan_row:
            for key, label in (("total_score", "gesamt_score"), ("short_score", "kurzfrist_score"),
                               ("long_score", "langfrist_score"), ("breakout_score", "breakout_score"),
                               ("rsi", "rsi"), ("pe", "kgv"), ("roe", "roe"),
                               ("short_float", "short_float_pct"), ("upside_pct", "analysten_potenzial_pct"),
                               ("sector", "sektor")):
                if scan_row.get(key) is not None:
                    ev[label] = scan_row.get(key)

        if stop_loss and price:
            ev["stop_abstand_pct"] = round((1.0 - stop_loss / price) * 100, 1)

        invested = sum(p.get("current_price", 0) * p.get("shares", 0)
                       for p in (depot.get("positions") or {}).values())
        ev["depot_cash"] = round(depot.get("cash", 0))
        ev["depot_investiert"] = round(invested)
        ev["depot_positionen"] = list((depot.get("positions") or {}).keys())
        return ev

    # ------------------------------------------------------------------
    # The three voices
    # ------------------------------------------------------------------
    def _call(self, system_instruction: str, prompt: str) -> Dict[str, Any]:
        model_name = self._get_fastest_model_name()
        for name in (model_name, "models/gemini-1.5-flash-latest"):
            try:
                model = genai.GenerativeModel(name, system_instruction=system_instruction)
                resp = model.generate_content(
                    prompt, generation_config={"response_mime_type": "application/json"})
                text = resp.text.strip().removeprefix('```json').removesuffix('```').strip()
                return json.loads(text)
            except Exception as exc:
                last = exc
        raise RuntimeError(f"Alle Modelle fehlgeschlagen: {last}")

    ADVOCATE_SYS = (
        "Du bist Analyst in einem quantitativen Hedgefonds und vertrittst AUSSCHLIESSLICH "
        "die Kaufseite. Du kennst das Urteil nicht und triffst keines. Argumentiere "
        "NUR mit den gelieferten Messwerten und benenne sie konkret mit Zahl. "
        "Erfinde keine Kennzahlen. Steht ein Wert auf null oder fehlt er, sag das. "
        "Antworte ausschliesslich mit validem JSON."
    )
    SCEPTIC_SYS = (
        "Du bist Risikoanalyst in einem quantitativen Hedgefonds und vertrittst "
        "AUSSCHLIESSLICH die Gegenseite. Du kennst das Urteil nicht und triffst keines. "
        "Argumentiere NUR mit den gelieferten Messwerten und benenne sie konkret mit Zahl. "
        "Erfinde keine Kennzahlen. Fehlende Daten sind selbst ein Risiko - benenne sie. "
        "Antworte ausschliesslich mit validem JSON."
    )
    JUDGE_SYS = (
        "Du bist Chief Risk Officer und entscheidest ueber die Freigabe von Kapital. "
        "Dir liegen zwei unabhaengige Plaedoyers und die Rohdaten vor. Du bist weder "
        "dem Kauf noch der Ablehnung verpflichtet - beide Ausgaenge sind gleichwertig. "
        "Antworte ausschliesslich mit validem JSON."
    )

    def _advocate(self, evidence: Dict[str, Any], mandate: str) -> str:
        r = self._call(self.ADVOCATE_SYS, f"""Mandat des Depots: {mandate}

Gemessene Fakten zum Kandidaten (JSON):
{json.dumps(evidence, indent=2, ensure_ascii=False)}

Nenne in hoechstens 3 Saetzen die staerksten Argumente FUER einen Kauf, jeweils
mit der konkreten Kennzahl, auf die du dich stuetzt.

Format: {{"case": "...", "staerkste_kennzahl": "..."}}""")
        return str(r.get("case", "")).strip() or "Kein Kaufargument formuliert."

    def _sceptic(self, evidence: Dict[str, Any], mandate: str) -> str:
        r = self._call(self.SCEPTIC_SYS, f"""Mandat des Depots: {mandate}

Gemessene Fakten zum Kandidaten (JSON):
{json.dumps(evidence, indent=2, ensure_ascii=False)}

Nenne in hoechstens 3 Saetzen die staerksten Argumente GEGEN einen Kauf, jeweils
mit der konkreten Kennzahl, auf die du dich stuetzt. Beruecksichtige auch
Klumpenrisiko im Depot und eine lueckenhafte Datenlage.

Format: {{"case": "...", "groesstes_risiko": "..."}}""")
        return str(r.get("case", "")).strip() or "Kein Gegenargument formuliert."

    def _judge(self, evidence: Dict[str, Any], mandate: str,
               bull: str, bear: str) -> Tuple[str, str, str]:
        r = self._call(self.JUDGE_SYS, f"""Mandat des Depots: {mandate}

Gemessene Fakten (JSON):
{json.dumps(evidence, indent=2, ensure_ascii=False)}

PLAEDOYER KAUFSEITE:
{bull}

PLAEDOYER GEGENSEITE:
{bear}

Entscheide: BUY oder REJECT.

Lehne ab, wenn mindestens einer dieser Punkte zutrifft:
- Die Bilanzqualitaet widerspricht dem Mandat des Depots (z.B. Piotroski unter 4/9
  oder Altman in der Distress Zone bei einem Langfrist-Kauf).
- Die Datenabdeckung liegt unter 50% und die Kaufseite stuetzt sich im Kern auf
  einen Baustein, der gar nicht gemessen wurde.
- Das Depot haelt bereits mehrere Werte desselben Sektors (Klumpenrisiko).
- Das Kaufargument ist reines Momentum ohne jede fundamentale oder
  Nachrichtenstuetze.
Andernfalls gib frei. Beide Ausgaenge sind zulaessig; entscheide nach Faktenlage,
nicht nach Vorsicht oder Optimismus.

Nenne in "decisive_factor" die EINE Kennzahl, die den Ausschlag gegeben hat,
mit ihrem Wert.

Format: {{"action": "BUY" oder "REJECT", "reasoning": "...", "decisive_factor": "..."}}""")
        action = str(r.get("action", "")).upper().strip()
        if action not in ("BUY", "REJECT"):
            action = "REJECT"
        return (action,
                str(r.get("reasoning", "Keine Begruendung geliefert.")).strip(),
                str(r.get("decisive_factor", "")).strip())

    DEPOT_MANDATE = {
        "short_term": ("Kurzfrist-Trading ueber Tage bis Wochen. Momentum und Ausbrueche "
                       "sind das Mandat; Bilanzqualitaet ist zweitrangig, aber grobe "
                       "fundamentale Schieflagen sind ein Ausschlussgrund."),
        "medium_term": ("Mittelfristiges Wachstum ueber 1-6 Monate. Trendstaerke UND "
                        "solide Fundamentaldaten werden gleichermassen erwartet."),
        "long_term": ("Langfristiges Qualitaetsinvestment ueber Jahre. Bilanzqualitaet, "
                      "Burggraben und Bewertung entscheiden; kurzfristiges Momentum "
                      "ist irrelevant."),
    }

    # ------------------------------------------------------------------
    def decide_trade(self, depot_id: str, candidate: Dict[str, Any], current_cash: float,
                     evidence: Optional[Dict[str, Any]] = None) -> Tuple[str, str, Dict[str, str]]:
        """Runs the tribunal. Returns (action, reason, debate_log)."""
        if not self.api_key or not GENAI_AVAILABLE:
            # Fail closed. This used to approve every trade, so a missing secret
            # silently switched the whole safety gate off instead of blocking.
            return ("REJECT",
                    "Kein GEMINI_API_KEY vorhanden - Tribunal kann nicht tagen, "
                    "Kauf wird sicherheitshalber abgelehnt.", {})

        sym = candidate.get("symbol", "Unbekannt")
        if evidence is None:
            evidence = {
                "symbol": sym,
                "preis": candidate.get("price"),
                "scanner_signal": candidate.get("reason", "")[:200],
                "depot_cash": round(current_cash),
            }
        mandate = self.DEPOT_MANDATE.get(depot_id, "Allgemeines Handelsmandat.")

        try:
            # Advocate and sceptic never see each other's text or any verdict.
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                f_bull = pool.submit(self._advocate, evidence, mandate)
                f_bear = pool.submit(self._sceptic, evidence, mandate)
                bull_case = f_bull.result()
                bear_case = f_bear.result()
            action, judge_reasoning, decisive = self._judge(evidence, mandate, bull_case, bear_case)
        except Exception as exc:
            bull_case = bear_case = f"Tribunal nicht zustande gekommen: {exc}"
            action = "REJECT"
            judge_reasoning = f"Fehler im Tribunal, Kauf abgelehnt: {exc}"
            decisive = ""

        self._log_to_db(sym, candidate.get("name", sym), depot_id,
                        bull_case, bear_case, judge_reasoning, action, decisive, evidence)

        return action, judge_reasoning, {"bull": bull_case, "bear": bear_case,
                                         "judge": judge_reasoning, "decisive": decisive}

    def _log_to_db(self, symbol, name, depot_id, bull, bear, judge, action,
                   decisive="", evidence=None):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            now_str = get_berlin_now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO tribunal_logs
                    (timestamp, symbol, name, depot_id, bull_case, bear_case,
                     judge_decision, action, decisive_factor, evidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (now_str, symbol, name, depot_id, bull, bear, judge, action, decisive,
                  json.dumps(evidence, ensure_ascii=False) if evidence else None))
            conn.commit()
            conn.close()
        except Exception:
            pass  # Logging must never block a decision

    @staticmethod
    def get_latest_logs(limit=20):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM tribunal_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = [dict(r) for r in cursor.fetchall()]
        except Exception:
            rows = []
        conn.close()
        return rows
