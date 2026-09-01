import os
import json
import sqlite3
import datetime
import concurrent.futures
from zoneinfo import ZoneInfo
from typing import Dict, Any, Tuple

try:
    import google.generativeai as genai
except ImportError:
    pass

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
            except:
                pass
                
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
        self._init_db()
        
    def _init_db(self):
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "portfolio.db")
        conn = sqlite3.connect(db_path)
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
        conn.commit()
        conn.close()

    def _get_fastest_model_name(self) -> str:
        if not hasattr(self, "_cached_model"):
            try:
                available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                if available:
                    # Prefer 1.5 flash if available, else take the first one
                    flash_models = [m for m in available if 'flash' in m.lower()]
                    self._cached_model = flash_models[0] if flash_models else available[0]
                else:
                    self._cached_model = "gemini-1.5-flash"
            except Exception:
                self._cached_model = "gemini-1.5-flash"
        return self._cached_model

    def decide_trade(self, depot_id: str, candidate: Dict[str, Any], current_cash: float) -> Tuple[str, str, Dict[str, str]]:
        """
        Runs the tribunal debate.
        Returns: action ('BUY', 'REJECT'), reason, debate_log
        """
        if not self.api_key:
            return "BUY", "Kein API Key gefunden, automatischer Buy-Bypass.", {}
            
        sym = candidate.get("symbol", "Unbekannt")
        reason = candidate.get("reason", "")
        price = candidate.get("price", 0.0)
        
        # Fastest available model dynamically resolved
        model_name = self._get_fastest_model_name()
        
        sys_prompt = "Du bist ein erfahrenes KI-Tribunal eines quantitativen Hedgefonds. Antworte IMMER nur mit validem JSON."
        
        prompt = f"""Kandidat: {sym} für Depot '{depot_id}'. Aktuelles Cash: {current_cash}€.
Signal vom Scanner: {reason} (Preis: {price}€)

Führe eine interne Debatte durch und fälle ein Urteil. 
- Formuliere in 1-2 Sätzen das stärkste bullische Argument (Chancen).
- Formuliere in 1-2 Sätzen das stärkste bärische Argument (Risiken).
- Triff eine Entscheidung (BUY oder REJECT) als Chief Risk Officer.
- Erlaube Trades mit gutem Momentum oder fundamentaler Stärke (sei nicht zu restriktiv). Lehne nur ab, wenn offensichtliche Red Flags vorliegen.

Antworte EXAKT in folgendem JSON-Format:
{{
  "bull_case": "...",
  "bear_case": "...",
  "action": "BUY",
  "reasoning": "..."
}}"""
        
        try:
            kwargs = {}
            if "1.5" in model_name or "flash" in model_name or "2.0" in model_name:
                kwargs["system_instruction"] = sys_prompt
            else:
                prompt = sys_prompt + "\n\n" + prompt
                
            model = genai.GenerativeModel(model_name, **kwargs)
            resp = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            res_json = json.loads(resp.text.strip().removeprefix('```json').removesuffix('```').strip())
            
            bull_case = res_json.get("bull_case", "Kein Bull Case generiert.")
            bear_case = res_json.get("bear_case", "Kein Bear Case generiert.")
            action = res_json.get("action", "REJECT").upper()
            if action not in ["BUY", "REJECT"]:
                action = "REJECT"
            judge_reasoning = res_json.get("reasoning", "Keine Begründung geliefert.")
            
        except Exception as e:
            try:
                # Try fallback
                fallback_model = "models/gemini-1.5-flash-latest"
                model = genai.GenerativeModel(fallback_model, system_instruction=sys_prompt)
                resp = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                res_json = json.loads(resp.text.strip().removeprefix('```json').removesuffix('```').strip())
                
                bull_case = res_json.get("bull_case", "Kein Bull Case generiert.")
                bear_case = res_json.get("bear_case", "Kein Bear Case generiert.")
                action = res_json.get("action", "REJECT").upper()
                if action not in ["BUY", "REJECT"]:
                    action = "REJECT"
                judge_reasoning = res_json.get("reasoning", "Keine Begründung geliefert.")
            except Exception as inner_e:
                bull_case = f"Fehler bei Analyse: {e}"
                bear_case = f"Fehler bei Analyse: {e}"
                action = "REJECT"
                judge_reasoning = f"Fehler bei Tribunal-Urteil: {e}"
        
        self._log_to_db(sym, depot_id, bull_case, bear_case, judge_reasoning, action)
        
        debate_log = {
            "bull": bull_case,
            "bear": bear_case,
            "judge": judge_reasoning
        }
        
        return action, judge_reasoning, debate_log

    def _log_to_db(self, symbol, depot_id, bull, bear, judge, action):
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "portfolio.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        now_str = get_berlin_now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO tribunal_logs (timestamp, symbol, depot_id, bull_case, bear_case, judge_decision, action)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (now_str, symbol, depot_id, bull, bear, judge, action))
        conn.commit()
        conn.close()
        
    @staticmethod
    def get_latest_logs(limit=20):
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "portfolio.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM tribunal_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = [dict(r) for r in cursor.fetchall()]
        except:
            rows = []
        conn.close()
        return rows
