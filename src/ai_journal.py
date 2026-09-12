import sqlite3
import json
import datetime
import os
from typing import Dict, Any, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    pass

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolio.db")
ALERTS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "realtime_alerts.json")
STRATEGY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "strategy.json")

from zoneinfo import ZoneInfo
BERLIN_TZ = ZoneInfo("Europe/Berlin")

def get_berlin_now() -> datetime.datetime:
    try:
        return datetime.datetime.now(BERLIN_TZ)
    except Exception:
        return datetime.datetime.utcnow() + datetime.timedelta(hours=2)

def _migrate_ai_journal_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(ai_journal)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if not columns:
        cursor.execute('''
            CREATE TABLE ai_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                depot_id TEXT NOT NULL,
                date TEXT NOT NULL,
                mode TEXT DEFAULT "daily",
                win_rate REAL,
                best_trade TEXT,
                worst_trade TEXT,
                reflection TEXT,
                lesson TEXT,
                missed_opportunities TEXT,
                param_updates TEXT,
                UNIQUE(depot_id, date, mode)
            )
        ''')
        conn.commit()
    conn.close()

# Run migration on import
_migrate_ai_journal_db()

# Safety bounds for each tunable parameter — the AI cannot go outside these ranges
PARAM_SAFETY_BOUNDS = {
    "daytrade_max_leverage":          {"min": 2.0,   "max": 15.0,  "step": 1.0},
    "daytrade_stop_loss_pct":         {"min": 0.05,  "max": 0.30,  "step": 0.01},
    "daytrade_max_risk_per_trade_pct":{"min": 0.005, "max": 0.03,  "step": 0.005},
    "daytrade_min_risk_reward_ratio": {"min": 1.5,   "max": 4.0,   "step": 0.5},
    "daytrade_max_daily_loss_pct":    {"min": 0.02,  "max": 0.10,  "step": 0.01},
    "daytrade_max_daily_trades":      {"min": 2,     "max": 10,    "step": 1},
    "daytrade_min_entry_score":       {"min": 40,    "max": 90,    "step": 5},
    "daytrade_trailing_breakeven_pct":{"min": 0.02,  "max": 0.08,  "step": 0.01},
    "daytrade_trailing_lock_pct":     {"min": 0.03,  "max": 0.15,  "step": 0.01},
    "daytrade_trailing_aggressive_pct":{"min": 0.05, "max": 0.25,  "step": 0.01},
    "daytrade_vix_defensive_threshold":{"min": 18.0, "max": 35.0,  "step": 1.0},
    "daytrade_vix_pause_threshold":   {"min": 25.0,  "max": 45.0,  "step": 1.0},
    "short_term_trailing_start_pct":  {"min": 3.0,   "max": 15.0,  "step": 1.0},
    "short_term_stop_loss_pct":       {"min": 0.05,  "max": 0.25,  "step": 0.01},
}


class AIJournalEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _load_strategy(self) -> Dict[str, Any]:
        """Loads current strategy parameters from strategy.json."""
        try:
            with open(STRATEGY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _save_strategy(self, params: Dict[str, Any]):
        """Writes updated strategy parameters to strategy.json."""
        with open(STRATEGY_FILE, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=4, ensure_ascii=False)

    def _get_depot_stats(self, depot_id: str, date_range: Optional[tuple] = None) -> Dict[str, Any]:
        """Calculates comprehensive trading statistics for a depot."""
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if date_range:
            cursor.execute(
                "SELECT * FROM trades WHERE depot_id = ? AND executed_at >= ? AND executed_at <= ? ORDER BY executed_at ASC",
                (depot_id, date_range[0], date_range[1] + " 23:59:59")
            )
        else:
            cursor.execute("SELECT * FROM trades WHERE depot_id = ? ORDER BY executed_at ASC", (depot_id,))

        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()

        sells = [t for t in trades if t.get("trade_type") == "SELL" and t.get("pnl") is not None]
        buys = [t for t in trades if t.get("trade_type") == "BUY"]

        if not sells:
            return {
                "total_buys": len(buys), "total_sells": 0, "win_rate": 0,
                "avg_win": 0, "avg_loss": 0, "expectancy": 0, "profit_factor": 0,
                "max_consecutive_losses": 0, "total_pnl": 0, "best_trade": "-",
                "worst_trade": "-", "trades": trades
            }

        wins = [t for t in sells if float(t["pnl"]) > 0]
        losses = [t for t in sells if float(t["pnl"]) <= 0]

        win_rate = len(wins) / len(sells) * 100 if sells else 0
        avg_win = sum(float(t["pnl"]) for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(float(t["pnl"]) for t in losses) / len(losses)) if losses else 0
        total_pnl = sum(float(t["pnl"]) for t in sells)

        # Expectancy
        expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)

        # Profit Factor
        gross_profit = sum(float(t["pnl"]) for t in wins) if wins else 0
        gross_loss = abs(sum(float(t["pnl"]) for t in losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Max consecutive losses
        max_streak, current_streak = 0, 0
        for t in sells:
            if float(t["pnl"]) <= 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        # Best/worst
        best = max(sells, key=lambda t: float(t["pnl"]))
        worst = min(sells, key=lambda t: float(t["pnl"]))

        return {
            "total_buys": len(buys),
            "total_sells": len(sells),
            "win_rate": round(win_rate, 1),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "expectancy": round(expectancy, 2),
            "profit_factor": round(profit_factor, 2),
            "max_consecutive_losses": max_streak,
            "total_pnl": round(total_pnl, 2),
            "best_trade": f"{best['symbol']} (+{float(best['pnl']):.2f}€, {float(best.get('pnl_pct', 0)):.1f}%)",
            "worst_trade": f"{worst['symbol']} ({float(worst['pnl']):.2f}€, {float(worst.get('pnl_pct', 0)):.1f}%)",
            "trades": trades
        }

    def get_trades(self, depot_id: str, date_prefix: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE depot_id = ? AND executed_at LIKE ? ORDER BY executed_at ASC", (depot_id, f"{date_prefix}%"))
        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return trades
        
    def get_weekly_trades(self, depot_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE depot_id = ? AND executed_at >= ? AND executed_at <= ? ORDER BY executed_at ASC", (depot_id, start_date, end_date + " 23:59:59"))
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

    def _apply_param_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and applies parameter updates from the AI within safety bounds.
        Returns a dict of what was actually changed."""
        if not updates or not isinstance(updates, dict):
            return {}

        current = self._load_strategy()
        applied = {}

        for param_name, new_value in updates.items():
            if param_name not in PARAM_SAFETY_BOUNDS:
                continue  # Unknown parameter, skip
            
            bounds = PARAM_SAFETY_BOUNDS[param_name]
            old_value = current.get(param_name)
            
            if old_value is None:
                continue

            try:
                new_value = type(old_value)(new_value)  # Cast to same type as current
            except (ValueError, TypeError):
                continue

            # Clamp to safety bounds
            new_value = max(bounds["min"], min(bounds["max"], new_value))

            # Only apply if actually different
            if new_value != old_value:
                current[param_name] = new_value
                applied[param_name] = {"old": old_value, "new": new_value}

        if applied:
            self._save_strategy(current)

        return applied

    def generate_retrospective(self, depot_id: str, mode="daily") -> Dict[str, Any]:
        """Generates an AI retrospective with real statistics and actionable parameter updates."""
        if not self.api_key:
            raise ValueError("Kein Gemini API Key vorhanden.")
            
        now = get_berlin_now()
        today_str = now.strftime("%Y-%m-%d")
        
        # 1. Gather real statistics
        if mode == "weekly":
            start_date = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            stats = self._get_depot_stats(depot_id, date_range=(start_date, today_str))
            date_label = f"{start_date} bis {today_str}"
            period_context = f"Wochenrückblick ({start_date} bis {today_str})"
        else:
            stats = self._get_depot_stats(depot_id, date_range=(today_str, today_str))
            date_label = today_str
            period_context = f"Tagesrückblick ({today_str})"

        # Also get all-time stats for context
        alltime_stats = self._get_depot_stats(depot_id)

        # 2. Load current strategy parameters
        current_params = self._load_strategy()

        # 3. Get missed alerts (daily only)
        traded_symbols = set(t.get("symbol") for t in stats["trades"])
        missed_alerts = self.get_todays_missed_alerts(today_str, traded_symbols) if mode == "daily" else []

        # 4. Build the bounds description for the prompt
        bounds_desc = "\n".join([
            f"  - {k}: aktuell={current_params.get(k, '?')}, min={v['min']}, max={v['max']}, step={v['step']}"
            for k, v in PARAM_SAFETY_BOUNDS.items()
        ])

        # 5. Build comprehensive prompt with REAL data
        prompt = f"""Du bist ein professioneller Quant-Analyst und Trading-Coach. Du analysierst die Performance 
eines algorithmischen Trading-Systems und schlägst KONKRETE Parameteränderungen vor.

## {period_context} — Depot: {depot_id}

### Heutige/Wöchentliche Statistiken:
- Abgeschlossene Trades (SELL): {stats['total_sells']}
- Win-Rate: {stats['win_rate']}%
- Durchschn. Gewinn pro Gewinner: {stats['avg_win']}€
- Durchschn. Verlust pro Verlierer: {stats['avg_loss']}€
- Expectancy pro Trade: {stats['expectancy']}€
- Profit Factor: {stats['profit_factor']}
- Gesamt-PnL: {stats['total_pnl']}€
- Max. Verluststrecke: {stats['max_consecutive_losses']} Trades in Folge
- Bester Trade: {stats['best_trade']}
- Schlechtester Trade: {stats['worst_trade']}

### Gesamtstatistik (seit Depotstart):
- Abgeschlossene Trades: {alltime_stats['total_sells']}
- Win-Rate: {alltime_stats['win_rate']}%
- Expectancy: {alltime_stats['expectancy']}€/Trade
- Profit Factor: {alltime_stats['profit_factor']}
- Gesamt-PnL: {alltime_stats['total_pnl']}€
- Max. Verluststrecke: {alltime_stats['max_consecutive_losses']}

### Aktuelle Strategie-Parameter:
{json.dumps(current_params, indent=2)}

### Erlaubte Parameterbereiche (Sicherheitsgrenzen):
{bounds_desc}

### Einzelne Trades im Zeitraum:
{json.dumps([{{
    'type': t.get('trade_type'), 'symbol': t.get('symbol'), 'pnl': t.get('pnl'),
    'pnl_pct': t.get('pnl_pct'), 'reason': t.get('reason', '')[:100], 'date': t.get('executed_at')
}} for t in stats['trades'][:30]], indent=2, ensure_ascii=False)}

### Verpasste Signale (nicht gehandelt):
{json.dumps(missed_alerts[:10], indent=2, ensure_ascii=False) if missed_alerts else "Keine verpassten Signale."}

## Deine Aufgabe:
1. Analysiere die Performance-Daten. Was sind die konkreten Schwachstellen?
2. Schlage KONKRETE Parameteränderungen vor, die die Expectancy verbessern.
   - Wenn die Win-Rate zu niedrig ist: Erhöhe den min_entry_score.
   - Wenn die Verluste zu groß sind: Senke den stop_loss_pct oder den max_leverage.
   - Wenn zu wenig gehandelt wird: Senke den min_entry_score oder erhöhe max_daily_trades.
   - Wenn der Profit Factor < 1.0: Die Strategie verliert Geld — aggressive Anpassung nötig.
3. Wenn keine Trades stattfanden: Analysiere WARUM und ob der min_entry_score zu hoch ist.
4. Ändere Parameter NUR wenn du eine klare datengetriebene Begründung hast. Wenn alles gut läuft, ändere NICHTS.

Antworte AUSSCHLIESSLICH im folgenden JSON-Format (keine Markdown-Blöcke):
{{
  "reflection": "Deine detaillierte Analyse der Trades und Schwachstellen...",
  "missed_opportunities": "Analyse der verpassten Signale und ob sie profitabel gewesen wären...",
  "lesson": "Die konkrete, datengetriebene Lektion...",
  "parameter_changes": {{
    "parameter_name": neuer_wert,
    "parameter_name2": neuer_wert2
  }},
  "change_reasoning": "Warum genau diese Parameter geändert werden, mit Bezug auf die Statistiken..."
}}

WICHTIG: "parameter_changes" muss ein JSON-Objekt sein mit den exakten Parameternamen aus strategy.json.
Wenn keine Änderungen nötig sind, setze "parameter_changes": {{}}.
"""

        # 6. Call Gemini
        response = None
        last_err = None
        
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as e:
            raise Exception(f"Konnte Modell-Liste nicht abrufen. API-Key ungültig? Fehler: {e}")

        if not available_models:
            raise Exception("Dein API-Key hat Zugriff auf 0 Modelle.")

        # Prioritize 2.0/1.5 models
        available_models.sort(key=lambda x: ('2.0' in x, '1.5' in x), reverse=True)

        for m_name in available_models[:5]:  # Try up to 5 models
            try:
                if '1.5' in m_name or '2.0' in m_name:
                    temp_model = genai.GenerativeModel(m_name, generation_config={"response_mime_type": "application/json"})
                else:
                    temp_model = genai.GenerativeModel(m_name)
                response = temp_model.generate_content(prompt)
                if response and response.text:
                    break
            except Exception as e:
                last_err = e
                response = None
                
        if not response:
            raise Exception(f"Alle {len(available_models)} Modelle fehlgeschlagen. Letzter Fehler: {last_err}")

        # 7. Parse response
        try:
            raw_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
            res_json = json.loads(raw_text)
        except Exception:
            res_json = {
                "reflection": "Fehler beim Parsen der KI-Antwort.",
                "missed_opportunities": "",
                "lesson": "",
                "parameter_changes": {},
                "change_reasoning": ""
            }

        # 8. Apply parameter changes (the core new feature!)
        param_changes = res_json.get("parameter_changes", {})
        applied_changes = self._apply_param_updates(param_changes)
        change_reasoning = res_json.get("change_reasoning", "")

        if applied_changes:
            param_log = "; ".join([f"{k}: {v['old']} -> {v['new']}" for k, v in applied_changes.items()])
            print(f"  ✅ PARAMETER ANGEPASST: {param_log}")
            print(f"  📝 Begründung: {change_reasoning[:200]}")
        else:
            print(f"  ℹ️ Keine Parameteränderungen vorgenommen.")

        # 9. Save journal entry
        def _safe_str(val):
            if isinstance(val, (dict, list)):
                return json.dumps(val, ensure_ascii=False)
            return str(val) if val else ""

        journal_entry = {
            "depot_id": depot_id,
            "date": date_label,
            "mode": mode,
            "win_rate": round(alltime_stats["win_rate"], 2),
            "best_trade": stats["best_trade"],
            "worst_trade": stats["worst_trade"],
            "reflection": _safe_str(res_json.get("reflection", "")),
            "missed_opportunities": _safe_str(res_json.get("missed_opportunities", "")),
            "lesson": _safe_str(res_json.get("lesson", "")),
            "param_updates": _safe_str(applied_changes) if applied_changes else _safe_str(param_changes)
        }

        self.save_journal_entry(journal_entry)
        return journal_entry

    def save_journal_entry(self, entry: Dict[str, Any]):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_journal (depot_id, date, mode, win_rate, best_trade, worst_trade, reflection, lesson, missed_opportunities, param_updates)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(depot_id, date, mode) DO UPDATE SET
                win_rate=excluded.win_rate,
                best_trade=excluded.best_trade,
                worst_trade=excluded.worst_trade,
                reflection=excluded.reflection,
                lesson=excluded.lesson,
                missed_opportunities=excluded.missed_opportunities,
                param_updates=excluded.param_updates
        ''', (
            entry["depot_id"], entry["date"], entry.get("mode", "daily"), entry["win_rate"], entry["best_trade"], entry["worst_trade"],
            entry["reflection"], entry["lesson"], entry["missed_opportunities"], entry.get("param_updates", "{}")
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
