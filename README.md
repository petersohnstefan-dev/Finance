# 📈 AI Börsen-Entscheidungs-System & Autonome Musterdepots

Ein umfassendes, datengestütztes Analyse- und Entscheidungssystem für Aktienmärkte in den **USA, Deutschland (DAX & SDAX-Nebenwerte) und Europa**.

---

## 🌟 Kernfunktionen

1. **🏆 Markt-Screener & Top-Rankings**:
   - Automatische Ranglisten über 130+ Aktien nach Gesamt-Score, Kurzfrist-Momentum, Langfrist-Qualität oder Analysten-Potenzial.
2. **🚨 Ausbruchs- & Katalysator-Radar (Biotech / Squeezes / Mid-Caps)**:
   - Filtert den Markt nach **Volumen-Explosionen (> 2x–3x Schnitt)**, **Bollinger-Squeezes** und **Leerverkäufer-Quoten (Short Float % / Days to Cover)** (nach dem *Moderna*-Muster).
3. **💼 Zwei autonome Musterdepots (je 10.000 € Startkapital)**:
   - **⚡ Kurz-/Mittelfristiges Trading-Depot**: Aktives Swing-Trading mit festem **Stop-Loss (-7%)** und **Take-Profit (+20%)**.
   - **🏛️ Langfristiges Investment-Depot**: Qualitätswerte mit starkem Burggraben (ROE > 15%), gesunder Bilanz und fairem KGV.
   - **Lückenloses Trade-Log**: Detaillierte Transaktions-Historie mit Zeitstempel, Einstandspreis, realisiertem Gewinn/Verlust und KI-Begründung.
4. **🔍 Einzelaktien-Tiefenanalyse**:
   - Interaktive Candlestick-Charts mit EMAs (20, 50, 200), Bollinger-Bändern, MACD, RSI, Bilanzen und Analysten-Konsens.
5. **☁️ 24/7 Autonomer Cloud-Betrieb via GitHub Actions**:
   - Vollautomatischer Markt-Scan & Handels-Check jeden Werktag um **08:00 Uhr (EU-Start)** und **15:00 Uhr (US-Start)** in der Cloud – völlig unabhängig vom heimischen PC.

---

## 🚀 Schnellstart (Lokal)

1. Abhängigkeiten installieren:
\\\ash
pip install -r requirements.txt
\\\

2. Web-Dashboard starten:
\\\ash
streamlit run app.py
\\\

3. Oder Einzelanalyse im Terminal ausführen:
\\\ash
python analyze.py --ticker NVDA
python analyze.py --ticker SAP.DE
\\\

---

## ☁️ 24/7 Kostenlos in der Cloud hosten (Streamlit Cloud)

1. Dieses GitHub-Repository öffnen.
2. Auf **[share.streamlit.io](https://share.streamlit.io)** kostenlos mit dem GitHub-Account anmelden.
3. Klicke auf **New App**, wähle dieses Repository (\petersohnstefan-dev/Finance\) und Main-File \pp.py\ aus.
4. Fertig! Du erhältst eine private, sichere Web-URL (z. B. \https://dein-name-finance.streamlit.app\), die du jederzeit am PC, Tablet oder Smartphone aufrufen kannst.
