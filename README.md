# 📈 AI Börsen-Entscheidungs-System & Autonome Musterdepots

Ein umfassendes, datengestütztes Analyse- und Entscheidungssystem für Aktienmärkte in den **USA, Deutschland (DAX & SDAX-Nebenwerte) und Europa**.

---

## 🌟 Kernfunktionen

1. **🏆 Markt-Screener & Top-Rankings**:
   - Automatische Ranglisten über 130+ Aktien nach Gesamt-Score, Kurzfrist-Momentum, Langfrist-Qualität oder Analysten-Potenzial.
2. **🚨 Ausbruchs- & Katalysator-Radar (Biotech / Squeezes / Mid-Caps)**:
   - Filtert den Markt nach **Volumen-Explosionen (> 2x–3x Schnitt)**, **Bollinger-Squeezes** und **Leerverkäufer-Quoten (Short Float % / Days to Cover)** (nach dem *Moderna*-Muster).
3. **💼 Zwei autonome Musterdepots (je 10.000 € Startkapital)**:
   - **⚡ Kurz-/Mittelfristiges Trading-Depot**: Trendfolgendes Swing-Trading mit **volatilitätsskaliertem Stop-Loss (2,5x ATR, 6-25%)** und **Chandelier-Trailing statt festem Take-Profit** – Verlierer werden eng begrenzt, Gewinner dürfen laufen.
   - **🏛️ Langfristiges Investment-Depot**: Qualitätswerte mit starkem Burggraben (ROE > 15%), gesunder Bilanz und fairem KGV.
   - **Lückenloses Trade-Log**: Detaillierte Transaktions-Historie mit Zeitstempel, Einstandspreis, realisiertem Gewinn/Verlust und KI-Begründung.
4. **🔍 Einzelaktien-Tiefenanalyse**:
   - Interaktive Candlestick-Charts mit EMAs (20, 50, 200), Bollinger-Bändern, MACD, RSI, Bilanzen und Analysten-Konsens.
5. **☁️ 24/7 Autonomer Cloud-Betrieb via GitHub Actions**:
   - Vollautomatischer Markt-Scan & Handels-Check jeden Werktag um **08:00 Uhr (EU-Start)** und **15:00 Uhr (US-Start)** in der Cloud – völlig unabhängig vom heimischen PC.

---

## 🚀 Schnellstart (Lokal)

1. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

2. Web-Dashboard starten:
```bash
streamlit run app.py
```

3. Oder Einzelanalyse im Terminal ausführen:
```bash
python analyze.py --ticker NVDA
python analyze.py --ticker SAP.DE
```

---

## 🔑 Optionale API-Schlüssel (alle kostenlos)

Das System läuft ohne diese Schlüssel vollständig. Fehlt einer, meldet der
betroffene Abschnitt „keine Daten“ – er erfindet **keine** Ersatzwerte.

| Secret | Wofür | Registrierung |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | KI-Tribunal und Lerntagebuch | [Google AI Studio](https://aistudio.google.com/) |
| `EIA_API_KEY` | US-Rohöl-Lagerbestände (wöchentlich) | [eia.gov/opendata](https://www.eia.gov/opendata/) |
| `FRED_API_KEY` | Inflation (CPI), Renditen, Realzins | [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` | Forum-Sentiment | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) (Typ *script*) |

Eintragen unter **Settings → Secrets and variables → Actions**.

Der **Crack-Spread** (Raffineriemarge) braucht keinen Schlüssel – er wird aus den
Futures CL=F, RB=F und HO=F berechnet.

---

## 🧪 Tests & Trockenläufe (ohne die Live-Daten anzufassen)

Schon das Erzeugen eines `PortfolioManager` öffnet `data/portfolio.db` und wendet
Migrationen an – ein scheinbar lesender Test verändert also die Arbeitskopie und
kann versehentlich über die Schreibvorgänge des Bots committet werden.

Deshalb laufen Tests über den Sandbox-Runner. Er kopiert `data/` in ein
temporäres Verzeichnis, biegt die Anwendung per `FINANCE_DATA_DIR` darauf um
(siehe `src/paths.py`) und prüft danach per Prüfsumme, dass das echte `data/`
unverändert ist:

```bash
python tools/sandbox_run.py mein_test.py
python tools/sandbox_run.py --keep mein_test.py   # Sandbox zum Nachsehen behalten
python tools/sandbox_run.py -m src.market_scanner
```

Wird eine echte Datei doch verändert, bricht der Runner mit Exit-Code 1 ab und
nennt die Datei – das bedeutet, dass ein Modul `src.paths` umgeht.

---

## ☁️ 24/7 Kostenlos in der Cloud hosten (Streamlit Cloud)

1. Dieses GitHub-Repository öffnen.
2. Auf **[share.streamlit.io](https://share.streamlit.io)** kostenlos mit dem GitHub-Account anmelden.
3. Klicke auf **New App**, wähle dieses Repository (\petersohnstefan-dev/Finance\) und Main-File \pp.py\ aus.
4. Fertig! Du erhältst eine private, sichere Web-URL (z. B. \https://dein-name-finance.streamlit.app\), die du jederzeit am PC, Tablet oder Smartphone aufrufen kannst.
