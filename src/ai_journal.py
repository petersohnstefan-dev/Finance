import sqlite3
import json
import datetime
import os
from typing import Dict, Any, List

try:
    import google.generativeai as genai
except ImportError:
    pass

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolio.db")
ALERTS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "realtime_alerts.json")

from zoneinfo import ZoneInfo
BERLIN_TZ = ZoneInfo("Europe/Berlin")

def get_berlin_now() -> datetime.datetime:
    try:
        return datetime.datetime.now(BERLIN_TZ)
    except Exception:
        return datetime.datetime.utcnow() + datetime.timedelta(hours=2)

class AIJournalEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def get_todays_trades(self, today_str: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE executed_at LIKE ? ORDER BY executed_at ASC", (f"{today_str}%",))
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

    def generate_daily_retrospective(self) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("Kein Gemini API Key vorhanden.")
            
        today_str = get_berlin_now().strftime("%Y-%m-%d")
        trades = self.get_todays_trades(today_str)
        
        traded_symbols = set([t.get("symbol") for t in trades])
        missed_alerts = self.get_todays_missed_alerts(today_str, traded_symbols)

        # Calculate basic stats
        wins = 0
        losses = 0
        best_trade = ""
        worst_trade = ""
        max_pnl = -999999.0
        min_pnl = 999999.0

        for t in trades:
            if t.get("trade_type") == "SELL" and t.get("pnl") is not None:
                p = float(t["pnl"])
                if p > 0:
                    wins += 1
                elif p < 0:
                    losses += 1
                
                if p > max_pnl:
                    max_pnl = p
                    best_trade = f"{t['name']} (+{p:.2f}€)"
                if p < min_pnl:
                    min_pnl = p
                    worst_trade = f"{t['name']} ({p:.2f}€)"

        total_closed = wins + losses
        win_rate = (wins / total_closed * 100.0) if total_closed > 0 else 0.0

        prompt = f"""Du bist eine KI-Trading-Assistenz. Es ist Ende des Handelstages.
Hier sind die Trades, die du heute ausgeführt hast:
{json.dumps(trades, indent=2)}

Hier sind Handels-Signale, die heute aufgetreten sind, die du aber NICHT gehandelt hast (z.B. wegen fehlendem Cash oder zu hohem Risiko):
{json.dumps(missed_alerts[:15], indent=2)}

Analysiere den heutigen Tag. 
1. Was lief gut? 
2. Wo lagst du falsch (z.B. Stop-Loss zu eng, falscher Hebel, Fehl-Trades)? 
3. Was war mit den nicht ausgeführten Signalen? Waren dort verpasste Chancen dabei, die sich rückblickend gelohnt hätten?
4. Welche Lektion/Regel ziehst du daraus für morgen?

Antworte ZWINGEND im folgenden reinen JSON-Format (keine Markdown-Blöcke drumherum):
{{
  "reflection": "Deine detaillierte Analyse der getätigten Trades...",
  "missed_opportunities": "Deine Analyse der verpassten Signale...",
  "lesson": "Die abgeleitete Regel für morgen..."
}}
"""
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-pro', 'gemini-1.5-pro-latest', 'gemini-pro']
        response = None
        last_err = None
        
        for m_name in models_to_try:
            try:
                if '1.5' in m_name:
                    temp_model = genai.GenerativeModel(m_name, generation_config={"response_mime_type": "application/json"})
                else:
                    temp_model = genai.GenerativeModel(m_name)
                response = temp_model.generate_content(prompt)
                break
            except Exception as e:
                last_err = e
                response = None
                
        if not response:
            raise Exception(f"Alle Modelle fehlgeschlagen. Letzter Fehler: {last_err}")
            
        try:
            res_json = json.loads(response.text.strip().removeprefix('```json').removesuffix('```').strip())
        except:
            res_json = {
                "reflection": "Fehler beim Generieren der Reflexion.",
                "missed_opportunities": "Fehler beim Generieren.",
                "lesson": "Fehler beim Generieren."
            }

        journal_entry = {
            "date": today_str,
            "win_rate": round(win_rate, 2),
            "best_trade": best_trade if total_closed > 0 else "-",
            "worst_trade": worst_trade if total_closed > 0 else "-",
            "reflection": res_json.get("reflection", ""),
            "missed_opportunities": res_json.get("missed_opportunities", ""),
            "lesson": res_json.get("lesson", "")
        }

        self.save_journal_entry(journal_entry)
        return journal_entry

    def save_journal_entry(self, entry: Dict[str, Any]):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_journal (date, win_rate, best_trade, worst_trade, reflection, lesson, missed_opportunities)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                win_rate=excluded.win_rate,
                best_trade=excluded.best_trade,
                worst_trade=excluded.worst_trade,
                reflection=excluded.reflection,
                lesson=excluded.lesson,
                missed_opportunities=excluded.missed_opportunities
        ''', (
            entry["date"], entry["win_rate"], entry["best_trade"], entry["worst_trade"],
            entry["reflection"], entry["lesson"], entry["missed_opportunities"]
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
