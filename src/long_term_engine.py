from typing import Dict, Any, List

class LongTermEngine:
    """Evaluates long-term investing quality, valuation, moat, and analyst consensus."""

    def evaluate(self, fundamentals: Dict[str, Any], consensus: Dict[str, Any]) -> Dict[str, Any]:
        score = 50.0  # Base neutral score
        signals: List[Dict[str, str]] = []

        pe = fundamentals.get("trailingPE")
        fwd_pe = fundamentals.get("forwardPE")
        peg = fundamentals.get("pegRatio")
        roe = fundamentals.get("returnOnEquity")
        profit_margin = fundamentals.get("profitMargins")
        debt_to_equity = fundamentals.get("debtToEquity")
        fcf_yield = fundamentals.get("fcfYield")
        div_yield = fundamentals.get("dividendYield")
        upside = consensus.get("upsideMeanPct")
        rec_mean = consensus.get("recommendationMean")

        # 1. Valuation: P/E & Forward P/E (max 20 pts)
        if pe is not None:
            if pe < 15:
                score += 15
                signals.append({"type": "bullish", "title": f"Günstiges KGV ({pe:.1f})", "desc": "Klassische Value-Bewertung"})
            elif pe < 25:
                score += 8
                signals.append({"type": "bullish", "title": f"Faires KGV ({pe:.1f})", "desc": "Im gesunden Marktschnitt"})
            elif pe > 45:
                score -= 12
                signals.append({"type": "warning", "title": f"Hohes KGV ({pe:.1f})", "desc": "Hohe Wachstumserwartungen bereits eingepreist"})

        # PEG Ratio
        if peg is not None:
            if 0 < peg <= 1.2:
                score += 12
                signals.append({"type": "bullish", "title": f"Attraktives PEG-Ratio ({peg:.2f})", "desc": "Günstige Bewertung relativ zum Gewinnwachstum"})
            elif peg > 2.5:
                score -= 8
                signals.append({"type": "warning", "title": f"Erhöhtes PEG-Ratio ({peg:.2f})", "desc": "Bewertung übersteigt das aktuelle Wachstumstempo"})

        # 2. Quality & Moat: ROE & Margen (max 20 pts)
        if roe is not None:
            if roe >= 20.0:
                score += 15
                signals.append({"type": "bullish", "title": f"Exzellente Eigenkapitalrendite ({roe:.1f}%)", "desc": "Starker Hinweis auf Wettbewerbsvorteil (Moat)"})
            elif roe >= 12.0:
                score += 8
                signals.append({"type": "bullish", "title": f"Solide Eigenkapitalrendite ({roe:.1f}%)", "desc": "Gute Rentabilität"})
            elif roe < 5.0:
                score -= 10
                signals.append({"type": "bearish", "title": f"Niedrige Eigenkapitalrendite ({roe:.1f}%)", "desc": "Schwache Kapitalverzinsung"})

        if profit_margin is not None:
            if profit_margin >= 20.0:
                score += 8
                signals.append({"type": "bullish", "title": f"Hohe Nettomarge ({profit_margin:.1f}%)", "desc": "Starke Preissetzungsmacht"})
            elif profit_margin < 0:
                score -= 15
                signals.append({"type": "bearish", "title": "Unprofitabel / Verlust", "desc": "Unternehmen wirtschaftet derzeit nicht profitabel"})

        # 3. Bilanz-Gesundheit: Debt-to-Equity & FCF (max 20 pts)
        if debt_to_equity is not None:
            if debt_to_equity < 0.8:
                score += 10
                signals.append({"type": "bullish", "title": f"Konservative Verschuldung ({debt_to_equity:.2f})", "desc": "Solide Bilanzstruktur"})
            elif debt_to_equity > 2.0:
                score -= 12
                signals.append({"type": "bearish", "title": f"Hohe Verschuldung ({debt_to_equity:.2f})", "desc": "Erhöhtes Zins- und Refinanzierungsrisiko"})

        if fcf_yield is not None:
            if fcf_yield >= 5.0:
                score += 10
                signals.append({"type": "bullish", "title": f"Starke Free-Cashflow-Rendite ({fcf_yield:.1f}%)", "desc": "Üppige Cash-Generierung für Reinvestition / Dividenden"})
            elif fcf_yield < 0:
                score -= 8
                signals.append({"type": "warning", "title": "Negativer Free Cashflow", "desc": "Cash-Burn oder hohe Investitionsphase"})

        # 4. Analysten-Konsens & Kursziel (max 20 pts)
        if upside is not None:
            if upside >= 20.0:
                score += 12
                signals.append({"type": "bullish", "title": f"Analysten-Kurspotenzial +{upside:.1f}%", "desc": f"Mittleres Kursziel: {consensus.get('targetMeanPrice')} {fundamentals.get('currency', 'USD')}"})
            elif upside <= -10.0:
                score -= 12
                signals.append({"type": "warning", "title": f"Kurs über Analystenziel ({upside:.1f}%)", "desc": "Aktie notiert über dem durchschnittlichen Analystenziel"})

        if rec_mean is not None:
            if rec_mean <= 1.8:
                score += 8
                signals.append({"type": "bullish", "title": "Analysten-Konsens: KAUFEN", "desc": f"Rating-Score: {rec_mean:.2f} (1=Strong Buy, 5=Sell)"})
            elif rec_mean >= 3.2:
                score -= 8
                signals.append({"type": "bearish", "title": "Analysten-Konsens: Halten / Verkaufen", "desc": f"Rating-Score: {rec_mean:.2f}"})

        # 5. Dividende
        if div_yield and div_yield > 0:
            signals.append({"type": "info", "title": f"Dividendenrendite: {div_yield:.2f}%", "desc": "Ausschüttungskomponente vorhanden"})

        # Normalize score
        final_score = max(0, min(100, round(score)))

        if final_score >= 75:
            status = "🏆 Erstklassiger Qualitäts-/Value-Wert"
        elif final_score >= 60:
            status = "✅ Solides Langfrist-Investment"
        elif final_score >= 45:
            status = "⚖️ Fair bewertet / Halteposition"
        elif final_score >= 30:
            status = "⚠️ Schwächere Fundamentaldaten / Vorsicht"
        else:
            status = "❌ Fundamental ungeeignet für Buy & Hold"

        return {
            "score": final_score,
            "status": status,
            "signals": signals
        }
