import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class BreakoutRadar:
    """Detects early signals of explosive moves, volatility breakouts, and short squeezes (like Moderna MRNA)."""

    def analyze_breakout_potential(self, df: pd.DataFrame, fundamentals: Dict[str, Any], forum_mentions: int = 0) -> Dict[str, Any]:
        if df.empty or len(df) < 25:
            return {"breakout_score": 0, "status": "Zu wenige Daten", "triggers": []}

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        triggers: List[Dict[str, str]] = []
        score = 0.0

        close = latest['Close']
        prev_close = prev['Close']
        daily_return_pct = ((close - prev_close) / prev_close) * 100.0
        
        vol_ratio = latest.get('Vol_Ratio', 1.0)
        rsi = latest.get('RSI_14', 50.0)
        bb_width = latest.get('BB_Width', 0.1)
        bb_upper = latest.get('BB_Upper', close)

        short_float = fundamentals.get('shortPercentOfFloat')
        short_ratio = fundamentals.get('shortRatio')
        squeeze_score = fundamentals.get('squeezeScore', 10.0)

        # 1. Volume Explosion (Der wichtigste Ausbruchsindikator)
        if vol_ratio >= 3.0:
            score += 35
            triggers.append({
                "type": "extreme",
                "title": f"🚨 Extremer Volumen-Schock ({vol_ratio:.1f}x)",
                "desc": "Massiver Zufluss von institutionellem Kapital oder Hype. Häufig Beginn einer großen Neubewertung."
            })
        elif vol_ratio >= 1.8:
            score += 20
            triggers.append({
                "type": "high",
                "title": f"⚡ Stark erhöhtes Handelsvolumen ({vol_ratio:.1f}x)",
                "desc": "Deutlicher Anstieg der Marktaktivität über dem 20-Tage-Schnitt."
            })

        # 2. Leerverkäufer & Short-Squeeze-Gefahr
        if short_float is not None and short_float >= 15.0:
            score += 25
            triggers.append({
                "type": "squeeze",
                "title": f"🪤 Hohe Leerverkaufsquote ({short_float:.1f}% Short Float)",
                "desc": "Hedgefonds halten hohe Short-Wetten. Bei positiven News droht ein panikartiges Eindecken (Short Squeeze)."
            })
        elif short_float is not None and short_float >= 8.0:
            score += 10
            triggers.append({
                "type": "squeeze",
                "title": f"⚠️ Erhöhte Short-Quote ({short_float:.1f}%)",
                "desc": "Spürbare Leerverkäufe am Markt vorhanden."
            })

        if short_ratio is not None and short_ratio >= 6.0:
            score += 15
            triggers.append({
                "type": "squeeze",
                "title": f"⏳ Hohe Eindeckungsdauer (Days to Cover: {short_ratio:.1f} Tage)",
                "desc": f"Leerverkäufer bräuchten über {short_ratio:.1f} volle Handelstage, um alle Short-Positionen glattzustellen."
            })

        # 3. Kursdynamik & Bollinger Band Breakout
        if close > bb_upper:
            score += 20
            triggers.append({
                "type": "high",
                "title": "💥 Ausbruch über oberes Bollinger Band",
                "desc": "Starker Impuls bricht aus der bisherigen Schwankungsbreite nach oben aus."
            })

        # 4. Volatilitäts-Kompression (Bollinger Squeeze)
        hist_bb_width = df['BB_Width'].tail(60)
        if len(hist_bb_width) > 20:
            min_width = hist_bb_width.quantile(0.15)
            if bb_width <= min_width:
                score += 15
                triggers.append({
                    "type": "setup",
                    "title": "🌀 Volatilitäts-Kompression (Bollinger Squeeze)",
                    "desc": "Extrem enge Handelsspanne. Historisch folgt darauf fast immer eine heftige Richtungsbewegung ('Gespanntes Gummiband')."
                })

        # 5. RSI Momentum Zündung (55 - 75)
        if 55 <= rsi <= 75 and daily_return_pct > 3.0:
            score += 10
            triggers.append({
                "type": "momentum",
                "title": f"🚀 Momentum-Zündung (RSI {rsi:.1f})",
                "desc": "Dynamischer Anstieg mit gesundem Beschleunigungspotenzial."
            })

        # 6. Foren- & Social-Buzz
        if forum_mentions >= 5:
            score += 15
            triggers.append({
                "type": "social",
                "title": f"🔥 Hoher Foren-Buzz ({forum_mentions} Erwähnungen)",
                "desc": "Starke Diskussionen auf Reddit / StockTwits. Treibstoff für spekulatives Momentum."
            })

        final_score = min(100, round(score))

        if final_score >= 70:
            status = "🚨 AKUTER AUSBRUCH / SQUEEZE-DYNAMIK"
        elif final_score >= 45:
            status = "⚡ ERHÖHTE AUSBRUCHS-CHANCE (Lauerstellung)"
        else:
            status = "😴 Normale Schwankung / Kein Squeeze"

        return {
            "breakout_score": final_score,
            "status": status,
            "daily_return_pct": round(daily_return_pct, 2),
            "vol_ratio": round(vol_ratio, 2),
            "short_float": short_float,
            "short_ratio": short_ratio,
            "squeeze_score": squeeze_score,
            "triggers": triggers
        }
