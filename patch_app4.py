import sys

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'sov_df.columns = ["Staat / Anleihe"' in line:
        lines[i] = '        sov_df.columns = ["Staat / Anleihe", "10-Jahres-Rendite", "Spread zu Dt. Bund", "Markt-Rolle / Datum"]\n'
    if 'st.dataframe(sov_df, use_container_width=True, hide_index=True)' in line:
        lines.insert(i + 1, '        st.info("ℹ️ **Hinweis zum Charting:** Eine historische Chart-Entwicklung ist in diesem Dashboard derzeit exklusiv für US-Staatsanleihen (den Weltzins) verfügbar, da die kostenfreie Live-Schnittstelle (Yahoo Finance) für die globalen Benchmark-Anleihen Europas und Asiens keine durchgehenden Zeitreihen ohne institutionelle API-Schlüssel liefert.")\n')
        break

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
