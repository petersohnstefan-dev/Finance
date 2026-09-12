import sys

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'h_tab1, h_tab2, h_tab3, h_tab4 = st.tabs([' in l:
        start_idx = i
        break

new_tabs = """            h_tab_dt, h_tab1, h_tab2, h_tab3, h_tab4 = st.tabs([
                "🔥 Daytrader-Depot (Intraday / 10x)",
                "⚡ 1. Kurzfrist-Depot (Tage–Wochen)",
                "📈 2. Mittelfrist-Depot (1–6 Monate)",
                "🏛️ 3. Langfrist-Depot (1–5+ Jahre)",
                "🪙 4. Rohstoff-, Anleihen- & FX-Regeln (GSR, Zinskurve, DXY & Carry-Trade)"
            ])

            with h_tab_dt:
                st.markdown('''
                #### 🔥 Daytrader-Depot (Aggressives Intraday-Trading & Momentum)
                **Ziel:** Sekunden- & Minuten-Ausbrüche blitzschnell reiten, maximaler Fokus auf Echtzeit-Volumen und große Hebel, kein Risiko über Nacht.

                | Dimension / Faktor | Gewichtung | Kriterien, Datenquellen & Schwellenwerte |
                | :--- | :---: | :--- |
                | **⚡ Echtzeit-Volumen-Spikes** | **50 %** | 1-Minuten Kurssprünge > +1,5 % getrieben durch plötzliche institutionelle Orders. |
                | **🚀 Derivate & Extrem-Hebel** | **30 %** | Ausschließlich Knock-Out Zertifikate (Long/Short) mit extremem Ziel-Hebel (ca. 10x). |
                | **🛡️ EOD Derisking** | **20 %** | Verhindert Über-Nacht-Gaps durch automatischen Verkauf profitabler Positionen vor Handelsende. |

                * **🟢 KAUF-Trigger:** Sofortiger Einstieg bei Erkennung eines Sub-Minute-Ausbruchs durch den *RealTimeBreakoutScanner*.
                * **💰 Positionsgröße:** Maximal 1.500 € pro Trade (kleinere Allokation aufgrund des hohen Hebels).
                * **🎯 Aggressives Profit-Ratcheting:** Ab +5 % Gewinn wird der Stop-Loss sofort auf +2 % (über Einstand) nachgezogen. Ab +10 % Gewinn greift ein extrem enger Trailing-Stop (nur noch 5 % Puffer zum Top).
                * **🚨 Intraday Notbremse:** Strenger initialer Knock-Out/Stop-Loss, um Totalverluste beim Daytrading abzufedern (max. -20 %).
                * **🛡️ End-of-Day (EOD) Derisking:** Befindet sich ein Trade nach 21:00 Uhr mit >2 % im Plus, wird er **zwingend verkauft**, um "Overnight-Risiko" (Gap-Downs am nächsten Morgen) vollständig auszuschließen.
                ''')
"""

# Replace lines i to i+5
end_idx = start_idx + 5
lines[start_idx:end_idx+1] = [new_tabs + "\n"]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    
print("Updated Strategy Handbook.")
