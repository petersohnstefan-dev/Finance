import sys

with open('src/ai_journal.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Modify get_todays_trades to get_trades
old_trade = """    def get_todays_trades(self, today_str: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE executed_at LIKE ? ORDER BY executed_at ASC", (f"{today_str}%",))
        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return trades"""

new_trade = """    def get_trades(self, date_prefix: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE executed_at LIKE ? ORDER BY executed_at ASC", (f"{date_prefix}%",))
        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return trades
        
    def get_weekly_trades(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE executed_at >= ? AND executed_at <= ? ORDER BY executed_at ASC", (start_date, end_date + " 23:59:59"))
        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return trades"""
content = content.replace(old_trade, new_trade)

# 2. Modify generate_daily_retrospective to generate_retrospective(mode)
old_gen_sig = """    def generate_daily_retrospective(self) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("Kein Gemini API Key vorhanden.")
            
        today_str = get_berlin_now().strftime("%Y-%m-%d")
        trades = self.get_todays_trades(today_str)
        
        traded_symbols = set([t.get("symbol") for t in trades])
        missed_alerts = self.get_todays_missed_alerts(today_str, traded_symbols)"""

new_gen_sig = """    def generate_retrospective(self, mode="daily") -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("Kein Gemini API Key vorhanden.")
            
        now = get_berlin_now()
        today_str = now.strftime("%Y-%m-%d")
        
        if mode == "weekly":
            start_date = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            trades = self.get_weekly_trades(start_date, today_str)
            traded_symbols = set([t.get("symbol") for t in trades])
            missed_alerts = [] # Keep prompt small for weekly
            date_label = f"{start_date} bis {today_str}"
            time_context = "Es ist das Ende der Handelswoche."
        else:
            trades = self.get_trades(today_str)
            traded_symbols = set([t.get("symbol") for t in trades])
            missed_alerts = self.get_todays_missed_alerts(today_str, traded_symbols)
            date_label = today_str
            time_context = "Es ist Ende des heutigen Handelstages." """
content = content.replace(old_gen_sig, new_gen_sig)

# 3. Modify prompt to ask for strategy updates
old_prompt = """        prompt = f\"\"\"Du bist eine KI-Trading-Assistenz. Es ist Ende des Handelstages.
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
\"\"\" """

new_prompt = """        
        # Load current strategy
        strat_file = os.path.join(os.path.dirname(__file__), "..", "data", "strategy.json")
        curr_strat = {}
        if os.path.exists(strat_file):
            try:
                with open(strat_file, "r", encoding="utf-8") as f:
                    curr_strat = json.load(f)
            except:
                pass

        prompt = f\"\"\"Du bist eine KI-Trading-Assistenz. {time_context}
Hier sind deine ausgeführten Trades in diesem Zeitraum:
{json.dumps(trades, indent=2)}

Hier sind Handels-Signale, die aufgetreten sind, die du aber NICHT gehandelt hast (nur bei Tages-Modus):
{json.dumps(missed_alerts[:15], indent=2)}

Hier sind deine aktuellen Trading-Parameter (strategy.json), nach denen der Bot handelt:
{json.dumps(curr_strat, indent=2)}

Analysiere diesen Zeitraum ({date_label}). 
1. Was lief gut? 
2. Wo lagst du falsch (z.B. Stop-Loss zu eng, falscher Hebel, Fehl-Trades)? 
3. Welche konkrete Lektion ziehst du daraus für die Zukunft?
4. Möchtest du Parameter anpassen? (z.B. daytrade_stop_loss_pct von 0.25 auf 0.30 erhöhen, daytrade_max_leverage senken, short_term_trailing_start_pct anpassen)

Antworte ZWINGEND im folgenden reinen JSON-Format (keine Markdown-Blöcke drumherum):
{{
  "reflection": "Deine detaillierte Analyse der Trades...",
  "missed_opportunities": "Deine Analyse der verpassten Signale (falls leer, schreibe 'N/A')...",
  "lesson": "Die abgeleitete Regel/Lektion...",
  "parameters_update": {{
      "daytrade_stop_loss_pct": 0.25,
      "daytrade_max_leverage": 30.0,
      "short_term_trailing_start_pct": 8.0,
      "short_term_stop_loss_pct": 0.15
  }}
}}
Wichtig: In parameters_update gibst du das komplette Dictionary zurück, bei dem du bei Bedarf Werte erhöht/gesenkt hast, die sich aus deinen Fehlern ergeben!
\"\"\" """
content = content.replace(old_prompt, new_prompt)

# 4. Modify saving block to include strategy file update and mode column
old_save = """        try:
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
        conn.close()"""

new_save = """        try:
            res_json = json.loads(response.text.strip().removeprefix('```json').removesuffix('```').strip())
            
            # Apply strategy update
            if "parameters_update" in res_json and isinstance(res_json["parameters_update"], dict):
                curr_strat.update(res_json["parameters_update"])
                with open(strat_file, "w", encoding="utf-8") as f:
                    json.dump(curr_strat, f, indent=4)
        except:
            res_json = {
                "reflection": "Fehler beim Generieren der Reflexion.",
                "missed_opportunities": "Fehler beim Generieren.",
                "lesson": "Fehler beim Generieren."
            }

        journal_entry = {
            "date": date_label,
            "mode": mode,
            "win_rate": round(win_rate, 2),
            "best_trade": best_trade if total_closed > 0 else "-",
            "worst_trade": worst_trade if total_closed > 0 else "-",
            "reflection": res_json.get("reflection", ""),
            "missed_opportunities": res_json.get("missed_opportunities", ""),
            "lesson": res_json.get("lesson", ""),
            "param_updates": json.dumps(res_json.get("parameters_update", {}))
        }

        self.save_journal_entry(journal_entry)
        return journal_entry

    def save_journal_entry(self, entry: Dict[str, Any]):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_journal (date, mode, win_rate, best_trade, worst_trade, reflection, lesson, missed_opportunities, param_updates)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                mode=excluded.mode,
                win_rate=excluded.win_rate,
                best_trade=excluded.best_trade,
                worst_trade=excluded.worst_trade,
                reflection=excluded.reflection,
                lesson=excluded.lesson,
                missed_opportunities=excluded.missed_opportunities,
                param_updates=excluded.param_updates
        ''', (
            entry["date"], entry.get("mode", "daily"), entry["win_rate"], entry["best_trade"], entry["worst_trade"],
            entry["reflection"], entry["lesson"], entry["missed_opportunities"], entry.get("param_updates", "{}")
        ))
        conn.commit()
        conn.close()"""

content = content.replace(old_save, new_save)

with open('src/ai_journal.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ai_journal.py logic for daily/weekly and strategy feedback.")
