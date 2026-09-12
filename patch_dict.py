import sys

with open('src/ai_journal.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_save = """        journal_entry = {
            "date": date_label,
            "mode": mode,
            "win_rate": round(win_rate, 2),
            "best_trade": best_trade if total_closed > 0 else "-",
            "worst_trade": worst_trade if total_closed > 0 else "-",
            "reflection": res_json.get("reflection", ""),
            "missed_opportunities": res_json.get("missed_opportunities", ""),
            "lesson": res_json.get("lesson", ""),
            "param_updates": json.dumps(res_json.get("parameters_update", {}))
        }"""

new_save = """        def _safe_str(val):
            if isinstance(val, (dict, list)):
                import json
                return json.dumps(val, ensure_ascii=False)
            return str(val) if val else ""

        journal_entry = {
            "date": date_label,
            "mode": mode,
            "win_rate": round(win_rate, 2),
            "best_trade": best_trade if total_closed > 0 else "-",
            "worst_trade": worst_trade if total_closed > 0 else "-",
            "reflection": _safe_str(res_json.get("reflection", "")),
            "missed_opportunities": _safe_str(res_json.get("missed_opportunities", "")),
            "lesson": _safe_str(res_json.get("lesson", "")),
            "param_updates": _safe_str(res_json.get("parameters_update", {}))
        }"""

content = content.replace(old_save, new_save)

with open('src/ai_journal.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ai_journal.py for safe strings.")
