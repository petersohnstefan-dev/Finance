from typing import Dict, Any

class DecisionSynthesizer:
    """Combines Short-Term Momentum and Long-Term Fundamental tracks into an actionable decision."""

    def synthesize(self, short_res: Dict[str, Any], long_res: Dict[str, Any], fundamentals: Dict[str, Any], consensus: Dict[str, Any]) -> Dict[str, Any]:
        s_score = short_res.get("score", 50)
        l_score = long_res.get("score", 50)

        # Combined composite score
        total_score = round((s_score * 0.4) + (l_score * 0.6))

        # Determine Recommendation Category
        if l_score >= 65 and s_score >= 65:
            action = "?? STARKE KAUFCHANCE (Beide Schienen Bullish)"
            action_desc = "Sowohl fundamentale Qualität als auch technisches Momentum sprechen klar für einen Einstieg."
            color = "green"
        elif l_score >= 65 and s_score < 45:
            action = "? LANGFRISTIGER QUALITY-BUY (Timing abwarten oder gestaffelt)"
            action_desc = "Exzellente fundamentale Qualität, aber kurzfristig im Abwärtstrend oder Konsolidierung. Chance für Tranchen-Kauf."
            color = "blue"
        elif l_score < 45 and s_score >= 65:
            action = "? REINER SWING-TRADE (Nur kurzfristig mit Stop-Loss)"
            action_desc = "Starkes Momentum & Chart-Ausbruch, aber fundamental schwächer bewertet. Nur für aktive Trader mit engem Risikomanagement."
            color = "orange"
        elif l_score >= 45 and s_score >= 45:
            action = "?? BEOBACHTEN / HALTEN (Neutral)"
            action_desc = "Ausgeglichenes Chance-Risiko-Verhältnis. Warten auf klare fundamentale oder technische Impulse."
            color = "gray"
        else:
            action = "?? VORSICHT / MEIDEN"
            action_desc = "Weder fundamental noch charttechnisch überzeugend. Erhöhtes Verlustrisiko."
            color = "red"

        return {
            "total_score": total_score,
            "short_score": s_score,
            "long_score": l_score,
            "action": action,
            "action_desc": action_desc,
            "color": color,
            "short_status": short_res.get("status"),
            "long_status": long_res.get("status"),
        }
