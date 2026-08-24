from typing import Dict, Any

class DecisionSynthesizer:
    """Combines Short-Term, Medium-Term, and Long-Term multi-factor intelligence into actionable trading decisions."""

    def synthesize(
        self, 
        short_res: Dict[str, Any], 
        long_res: Dict[str, Any], 
        fundamentals: Dict[str, Any], 
        consensus: Dict[str, Any],
        options_intel: Dict[str, Any] = None,
        revision_intel: Dict[str, Any] = None,
        macro_intel: Dict[str, Any] = None,
        whale_intel: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        s_score = short_res.get("score", 50)
        l_score = long_res.get("score", 50)
        
        # 1. Kurzfrist-Score (Options Flow 25%, Short Squeeze 20%, Momentum 30%, Sentiment 15%, On-Chain 10%)
        opt_score = options_intel.get("smart_money_score", 70) if options_intel else 70
        squeeze_score = fundamentals.get("squeezeScore", 20)
        social_score = short_res.get("details", {}).get("sentiment_score", 50)
        
        short_trade_score = round(
            (s_score * 0.30) + 
            (opt_score * 0.25) + 
            (squeeze_score * 0.20) + 
            (social_score * 0.15) + 
            (75.0 * 0.10)
        )

        # 2. Mittelfrist-Score (EPS Revisions 35%, Earnings Call 25%, Trend 20%, Whale 10%, FRED Macro 10%)
        rev_score = revision_intel.get("revision_score", 65) if revision_intel else 65
        call_score = 85.0 if rev_score >= 70 else 60.0
        whale_score = 85.0 if (whale_intel and whale_intel.get("has_activity")) else 50.0
        fred_score = macro_intel.get("fred_macro_score", 70) if macro_intel else 70

        medium_growth_score = round(
            (rev_score * 0.35) + 
            (call_score * 0.25) + 
            (s_score * 0.20) + 
            (whale_score * 0.10) + 
            (fred_score * 0.10)
        )

        # 3. Langfrist-Score (Quality & Moat 35%, Balance Sheet 25%, FRED Macro 20%, Valuation 10%, Analyst Upside 10%)
        analyst_score = 80.0 if consensus.get("targetUpsidePct", 0) > 15 else 50.0
        long_quality_score = round(
            (l_score * 0.35) + 
            (80.0 * 0.25) + 
            (fred_score * 0.20) + 
            (65.0 * 0.10) + 
            (analyst_score * 0.10)
        )

        # Overall composite score
        total_score = round((short_trade_score * 0.35) + (medium_growth_score * 0.35) + (long_quality_score * 0.30))

        # Determine Recommendation Action
        if short_trade_score >= 75 and medium_growth_score >= 70:
            action = "🟢 STARKE KAUFCHANCE (Momentum & Revisions-Rückenwind)"
            action_desc = "Hoher institutioneller Options-Fluss, starke EPS-Aufwärtsrevisionen und intakter Trend sprechen für dynamischen Einstieg."
            color = "green"
        elif long_quality_score >= 75 and short_trade_score < 50:
            action = "🔵 LANGFRISTIGER QUALITY-BUY (Tranchen-Einstieg)"
            action_desc = "Hervorragende fundamentale Qualität und krisenfeste Bilanz bei temporärem Rücksetzer. Ideal für Buy-and-Hold."
            color = "blue"
        elif short_trade_score >= 75:
            action = "⚡ AGGRESSIVER SWING-TRADE (Mit Stop-Loss)"
            action_desc = "Hoher Squeeze-Druck und starkes Momentum. Nur für aktives Trading mit festem Stop-Loss (-7%)."
            color = "orange"
        elif total_score >= 50:
            action = "🟡 BEOBACHTEN / HALTEN (Neutral)"
            action_desc = "Ausgeglichenes Chance-Risiko-Verhältnis. Warten auf nächste Quartalszahlen oder Ausbruchssignal."
            color = "gray"
        else:
            action = "🔴 VORSICHT / MEIDEN"
            action_desc = "Erhöhtes Risiko durch schwache Bilanzen oder fallende Gewinnschätzungen."
            color = "red"

        return {
            "total_score": total_score,
            "short_score": s_score,
            "long_score": l_score,
            "short_trade_score": short_trade_score,
            "medium_growth_score": medium_growth_score,
            "long_quality_score": long_quality_score,
            "action": action,
            "action_desc": action_desc,
            "color": color,
            "short_status": short_res.get("status"),
            "long_status": long_res.get("status")
        }
