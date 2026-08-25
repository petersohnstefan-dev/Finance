"""Quantitative Seasonality, Day-of-Week Patterns & Macro Event Risk Engine."""

import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, List

BERLIN_TZ = ZoneInfo("Europe/Berlin")

def get_berlin_now() -> datetime.datetime:
    return datetime.datetime.now(BERLIN_TZ)

# Key Recurring Central Bank & Macro Calendar Events
MACRO_CALENDAR_EVENTS = [
    {"event": "FOMC Zinsentscheid (US-Fed)", "frequency": "8x jährlich (Mittwochs 20:00 Uhr)", "impact": "🔥 EXTREM HOCH", "rule": "Keine neuen Hebel-Trades 24h vor Zinsentscheid"},
    {"event": "EZB Ratssitzung & Zinsentscheid", "frequency": "8x jährlich (Donnerstags 14:15 Uhr)", "impact": "🔥 EXTREM HOCH", "rule": "Erhöhte EUR-Volatilität; Stopps vor 14:15 Uhr nachziehen"},
    {"event": "US Non-Farm Payrolls (NFP Arbeitsmarkt)", "frequency": "1. Freitag im Monat (14:30 Uhr)", "impact": "⚡ HOCH", "rule": "Whipsaw-Gefahr um 14:30; abwarten bis 15:00 Uhr"},
    {"event": "US CPI Inflationsbericht", "frequency": "Monatlich um den 12.–15. (14:30 Uhr)", "impact": "⚡ HOCH", "rule": "Renditen- und Dollar-Impulsgeber"},
    {"event": "Großer Verfallstag (Triple Witching / Hexensabbat)", "frequency": "3. Freitag im März, Juni, Sept, Dez", "impact": "🎯 HOCH", "rule": "Options-Pinning & künstliche Kurshaltepunkte an Strikes"}
]

class MarketSeasonalityEngine:
    """Calculates statistical day-of-week biases, calendar anomalies, and macro event risk modifiers."""

    @staticmethod
    def get_current_seasonality_analysis() -> Dict[str, Any]:
        now = get_berlin_now()
        weekday_idx = now.weekday()  # 0=Monday, 4=Friday, 6=Sunday
        day_of_month = now.day
        hour = now.hour

        weekday_names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        curr_weekday = weekday_names[weekday_idx]

        # 1. Day-of-Week Seasonality Bias
        day_bias = {}
        if weekday_idx == 0:  # Monday
            day_bias = {
                "name": "Montags-Effekt (Monday Sentiment Drift)",
                "status": "🟡 Moderat / Abwartend",
                "score_modifier": 0,
                "description": "Erste Reaktion auf Wochenend-News. Europäischer Vormittag oft seitwärts, bis die US-Märkte um 15:30 Uhr die Wochenrichtung vorgeben.",
                "trading_rule": "Ausbrüche erst nach 15:30 Uhr handeln, wenn US-Volumen bestätigt."
            }
        elif weekday_idx == 1:  # Tuesday
            day_bias = {
                "name": "Turnaround-Tuesday (Rebound-Statistik)",
                "status": "🟢 Bullisch für Rebounds (+10 Score)",
                "score_modifier": +10,
                "description": "Statistisch der Tag mit der höchsten Trefferquote für Gegenbewegungen (Mean-Reversion) nach montäglichen Abverkäufen.",
                "trading_rule": "Überverkaufte Qualitätsaktien (RSI < 40) aggressiver auf Rebound kaufen."
            }
        elif weekday_idx == 2:  # Wednesday
            day_bias = {
                "name": "Mid-Week Trend Continuation",
                "status": "🟢 Starker Trend-Tag",
                "score_modifier": +5,
                "description": "Höchste Liquidität der Woche bei institutionellen Orderbüchern. Primäre Trendfortsetzungen verlaufen mittwochs am saubersten.",
                "trading_rule": "Trendfolge-Signale (EMA 50 Breakouts) haben die höchste statistische Zuverlässigkeit."
            }
        elif weekday_idx == 3:  # Thursday
            day_bias = {
                "name": "Donnerstags-Momentum",
                "status": "🟢 Hohe Aktivität",
                "score_modifier": +5,
                "description": "Häufiger Tag für EZB-Zinsentscheide und wöchentliche US-Erstanträge auf Arbeitslosenhilfe (14:30 Uhr).",
                "trading_rule": "US-Vorbörse um 14:30 Uhr auf Zins- und Dollar-Impulse überwachen."
            }
        elif weekday_idx == 4:  # Friday
            if hour >= 16:
                day_bias = {
                    "name": "Freitags-Derisking & Weekend Gap Risk",
                    "status": "🔴 Vorsichtig / Defensiv (-15 Score auf neue Hebel)",
                    "score_modifier": -15,
                    "description": "Institutionelle Trader und Hedgefonds schließen vor dem Wochenende Hebelpositionen, um unkalkulierbare Wochenend-News (Geopolitik, Kriege) zu meiden.",
                    "trading_rule": "Ab 16:00 Uhr keine neuen Knock-Outs mit engem Puffer (< 10%) mehr kaufen! Gewinne sichern."
                }
            else:
                day_bias = {
                    "name": "Freitags-Vormittag (Positionsbereinigung)",
                    "status": "🟡 Neutral / Fokus auf Teilgewinnmitnahmen",
                    "score_modifier": -5,
                    "description": "Solider Handel am Vormittag, aber Vorbereitung auf Wochenend-Risikoreduzierung am späten Nachmittag.",
                    "trading_rule": "Stopps bei Gewinnern nachziehen und Gewinne sichern."
                }
        else:  # Weekend
            day_bias = {
                "name": "Wochenende (Börsenpause / Krypto 24/7)",
                "status": "🪙 Krypto-Fokus",
                "score_modifier": 0,
                "description": "Traditionelle Börsen geschlossen. Krypto-Märkte handeln mit dünnerem Orderbuch (erhöhte Volatilität).",
                "trading_rule": "Krypto-Bewegungen aufmerksam beobachten (oft Vorbote für den Aktien-Montag)."
            }

        # 2. Turn-of-the-Month (TOM) Effect
        is_tom = (day_of_month >= 27 or day_of_month <= 4)
        tom_info = {
            "is_active": is_tom,
            "name": "Turn-of-the-Month (TOM-Effekt)",
            "status": "🟢 Aktiv (+8 Punkte Bonus)" if is_tom else "⚪ Inaktiv (Monatsmitte)",
            "score_modifier": 8 if is_tom else 0,
            "description": "Die letzten 3 Tage des Monats und die ersten 4 Tage des Folgemonats weisen historisch eine statistisch signifikante Outperformance auf (Zuflüsse durch monatliche Sparpläne & Pensionskassen)."
        }

        # 3. Quarterly / Seasonal Context
        month = now.month
        quarter = (month - 1) // 3 + 1
        seasonal_context = ""
        if month in [11, 12, 1]:
            seasonal_context = "🎅 Starke Jahresendrallye & Neujahrs-Effekt (historisch bullischstes Quartal)"
        elif month in [8, 9]:
            seasonal_context = "🍂 Spätsommer / September-Saisonalität (historisch volatilster Monat des Jahres)"
        elif month in [4, 5]:
            seasonal_context = "🌱 Frühjahrs-Dividendensaison in Europa & 'Sell in May'-Überprüfung"
        else:
            seasonal_context = "📊 Ausgewogene Quartals-Saisonalität"

        total_seasonal_boost = day_bias["score_modifier"] + tom_info["score_modifier"]

        return {
            "current_time_berlin": now.strftime("%Y-%m-%d %H:%M:%S (MESZ / Berlin)"),
            "weekday": curr_weekday,
            "day_bias": day_bias,
            "tom_anomaly": tom_info,
            "seasonal_context": seasonal_context,
            "total_score_modifier": total_seasonal_boost,
            "events_calendar": MACRO_CALENDAR_EVENTS
        }

if __name__ == "__main__":
    eng = MarketSeasonalityEngine()
    analysis = eng.get_current_seasonality_analysis()
    print("Saisonalitaets-Analyse:", analysis["weekday"])
    print("Tages-Bias:", analysis["day_bias"])
    print("TOM-Effekt:", analysis["tom_anomaly"])
