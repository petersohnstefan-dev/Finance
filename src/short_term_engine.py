import pandas as pd
from typing import Dict, Any, List

class ShortTermEngine:
    """Evaluates short- to medium-term swing & momentum opportunities."""

    def evaluate(self, df: pd.DataFrame, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        if df.empty or len(df) < 20:
            return {"score": 50, "status": "Zu wenige Daten", "signals": [], "details": {}}

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        score = 50.0  # Base neutral score
        signals: List[Dict[str, str]] = []

        close = latest['Close']
        ema_20 = latest['EMA_20']
        ema_50 = latest['EMA_50']
        sma_200 = latest['SMA_200'] if not pd.isna(latest['SMA_200']) else ema_50
        rsi = latest['RSI_14']
        macd = latest['MACD']
        macd_hist = latest['MACD_Hist']
        macd_prev_hist = prev['MACD_Hist']
        bb_upper = latest['BB_Upper']
        bb_lower = latest['BB_Lower']
        vol_ratio = latest['Vol_Ratio']

        # 1. Trend Filter (EMA 20 / EMA 50 / SMA 200) - max 25 pts
        if close > ema_20 and ema_20 > ema_50:
            score += 15
            signals.append({"type": "bullish", "title": "Starker Aufwärtstrend", "desc": "Kurs notiert über EMA 20 & EMA 50"})
        elif close < ema_20 and ema_20 < ema_50:
            score -= 15
            signals.append({"type": "bearish", "title": "Abwärtstrend", "desc": "Kurs unter EMA 20 & EMA 50"})
        
        if close > sma_200:
            score += 10
            signals.append({"type": "bullish", "title": "Über 200-Tage-Linie", "desc": "Langfristiger Aufwärtstrend intakt"})
        else:
            score -= 10
            signals.append({"type": "bearish", "title": "Unter 200-Tage-Linie", "desc": "Vorsicht vor übergeordnetem Bärenmarkt"})

        # 2. Momentum & RSI (14) - max 25 pts
        if rsi < 30:
            score += 15
            signals.append({"type": "bullish", "title": f"RSI Überverkauft ({rsi:.1f})", "desc": "Klassische Chance auf technischen Rebound"})
        elif 45 <= rsi <= 65:
            score += 10
            signals.append({"type": "bullish", "title": f"Gesunder RSI ({rsi:.1f})", "desc": "Stabiles Momentum ohne Überhitzung"})
        elif rsi > 75:
            score -= 15
            signals.append({"type": "warning", "title": f"RSI Stark Überkauft ({rsi:.1f})", "desc": "Erhöhte Rückschlagsgefahr auf kurze Sicht"})

        # 3. MACD Momentum Crossover - max 15 pts
        if macd_hist > 0 and macd_prev_hist <= 0:
            score += 15
            signals.append({"type": "bullish", "title": "MACD Kaufsignal (Bullish Cross)", "desc": "Momentum dreht dynamisch ins Positive"})
        elif macd_hist > 0:
            score += 8
            signals.append({"type": "bullish", "title": "Positives MACD-Momentum", "desc": "MACD notiert über Signallinie"})
        elif macd_hist < 0 and macd_prev_hist >= 0:
            score -= 15
            signals.append({"type": "bearish", "title": "MACD Verkaufssignal (Bearish Cross)", "desc": "Momentum dreht nach unten"})
        else:
            score -= 8

        # 4. Bollinger Bänder - max 10 pts
        if close <= bb_lower * 1.01:
            score += 10
            signals.append({"type": "bullish", "title": "Am unteren Bollinger Band", "desc": "Mögliche Unterstützungszone erreicht"})
        elif close >= bb_upper * 0.99:
            score -= 8
            signals.append({"type": "warning", "title": "Am oberen Bollinger Band", "desc": "Bandbreite ausgereizt"})

        # 5. Volumen-Bestätigung - max 10 pts
        if vol_ratio > 1.4:
            if close > prev['Close']:
                score += 10
                signals.append({"type": "bullish", "title": f"Hohes Kaufvolumen ({vol_ratio:.1f}x)", "desc": "Überdurchschnittliches Interesse von Käufern"})
            else:
                score -= 10
                signals.append({"type": "bearish", "title": f"Hohes Abgabevolumen ({vol_ratio:.1f}x)", "desc": "Verkaufsdruck mit erhöhtem Volumen"})

        # 6. Sentiment (StockTwits / Social) - max 15 pts
        if sentiment_data.get("available"):
            bull_pct = sentiment_data.get("bullish_pct", 50)
            if bull_pct > 70:
                score += 10
                signals.append({"type": "bullish", "title": f"Social Sentiment Sehr Bullish ({bull_pct:.0f}%)", "desc": "Hohe positive Stimmung in der Community"})
            elif bull_pct < 35:
                score -= 10
                signals.append({"type": "bearish", "title": f"Social Sentiment Bearish ({bull_pct:.0f}%)", "desc": "Überwiegend negative Stimmung"})

        # Normalize score between 0 and 100
        final_score = max(0, min(100, round(score)))

        # Status label
        if final_score >= 75:
            status = "?? Stark Bullish / Kauf-Setup"
        elif final_score >= 60:
            status = "?? Moderat Bullish / Trendfolge"
        elif final_score >= 45:
            status = "?? Neutral / Konsolidierung"
        elif final_score >= 30:
            status = "?? Vorsicht / Schwächetendenz"
        else:
            status = "?? Stark Bearish / Meiden"

        return {
            "score": final_score,
            "status": status,
            "signals": signals,
            "metrics": {
                "rsi": round(rsi, 2),
                "close": round(close, 2),
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "sma_200": round(sma_200, 2) if not pd.isna(sma_200) else None,
                "macd": round(macd, 2),
                "macd_hist": round(macd_hist, 2),
                "vol_ratio": round(vol_ratio, 2)
            }
        }
