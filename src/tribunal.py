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
        
        # Fastest available flash model
        model_name = "gemini-1.5-flash"
        
        sys_prompt_base = "Du bist ein Top-Analyst in einem Hedgefonds. Antworte in 1-2 extrem präzisen Sätzen auf Deutsch. Komm direkt zur Sache, keine Höflichkeitsfloskeln."
        
        bull_prompt = f"Scanner meldet Kaufsignal für {sym} bei {price}€. Grund: {reason}. Bringe das stärkste bullische Argument vor, warum wir den Trade JETZT machen müssen (Upside, Momentum)."
        bear_prompt = f"Scanner meldet Kaufsignal für {sym} bei {price}€. Grund: {reason}. Dein Job: Zerstöre dieses Signal. Finde die Schwachstellen, Makro-Risiken oder zeige auf, warum es eine Bullenfalle ist."
        
        def call_llm(prompt: str) -> str:
            try:
                model = genai.GenerativeModel(model_name, system_instruction=sys_prompt_base)
                resp = model.generate_content(prompt)
                return resp.text.strip()
            except Exception as e:
                return f"Fehler bei Analyse: {e}"

        # Run Bull and Bear in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            bull_future = executor.submit(call_llm, bull_prompt)
            bear_future = executor.submit(call_llm, bear_prompt)
            bull_case = bull_future.result()
            bear_case = bear_future.result()
            
        judge_prompt = f"""Du bist der Chief Risk Officer (Judge).
Kandidat: {sym} für Depot '{depot_id}'. Aktuelles Cash: {current_cash}€. 
Signal: {reason}

Argument BULL:
{bull_case}

Argument BEAR:
{bear_case}

Entscheide knallhart: KAUFEN (BUY) oder ABLEHNEN (REJECT)? Bist du unsicher, lehne ab!
Antworte im JSON Format:
{{"action": "BUY" oder "REJECT", "reasoning": "Deine 1-Satz-Begründung"}}
"""
        
        try:
            judge_model = genai.GenerativeModel(model_name, system_instruction="Du bist der Judge. Antworte IMMER nur mit validem JSON.")
            judge_resp = judge_model.generate_content(judge_prompt, generation_config={"response_mime_type": "application/json"})
            res_json = json.loads(judge_resp.text.strip().removeprefix('```json').removesuffix('```').strip())
            
            action = res_json.get("action", "REJECT").upper()
            if action not in ["BUY", "REJECT"]:
                action = "REJECT"
            judge_reasoning = res_json.get("reasoning", "Keine Begründung geliefert.")
            
        except Exception as e:
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
