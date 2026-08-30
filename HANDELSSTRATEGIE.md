# 📈 Quantitative & KI-gesteuerte Handelsstrategie

Dieses Dokument beschreibt die Architektur und die algorithmischen/entscheidungsbasierten Regeln des **Multi-Agenten Trading-Systems**. Das System verwaltet vier dedizierte Musterdepots, die autonom scannen, Risiko berechnen, debattieren und Trades ausführen.

---

## 1. Das Anlageuniversum
Das System scannt kontinuierlich ein stark diversifiziertes Universum aus über 300 Werten:
*   **Kryptowährungen:** (z.B. BTC, ETH, SOL)
*   **ETFs:** Breite Indizes (SPY, QQQ), Sektoren (SMH, XLK) und Anleihen (TLT, SHY)
*   **US Tech & Growth:** S&P 500 Leaders, Nasdaq 100, Mid-Cap AI
*   **Europa & Deutschland:** DAX, MDAX, SDAX, EU Bluechips
*   **Rohstoffe:** Gold, Silber, Öl, Gas

---

## 2. Der Entscheidungsprozess (Multi-Agenten KI-Tribunal)
Kein Trade wird mehr blind vom Scanner ausgeführt. Das System nutzt einen dezentralen **KI-Tribunal-Prozess**:
1.  **Scanner-Signal:** Die quantitativen Scanner (Breakout, Insider, Makro, Sentiment) identifizieren einen Kandidaten.
2.  **Die Debatte (Parallel):**
    *   🐂 **Der Bulle:** Sucht das stärkste Kaufargument (Momentum, Flow, Katalysator).
    *   🐻 **Der Bär:** Sucht nach Risiken (Widerstände, Überkauf, Makro-Schwäche).
3.  **Das Urteil (Chief Risk Officer):** Ein dritter Agent (Judge) bewertet die Argumente und fällt eine unumstößliche JSON-Entscheidung (`BUY` oder `REJECT`).
*(Jedes Urteil wird transparent in der `tribunal_logs`-Datenbank gespeichert).*

---

## 3. Dynamisches Risk Management
Das Kapital wird nicht linear verteilt, sondern passt sich strikt der Marktlage und der Schwankung an.

*   **Market Regime Switching (Bullen- vs. Bärenmarkt):**
    Vor jedem Trade wird der S&P 500 (SPY) gegen seine 200-Tage-Linie (SMA 200) gemessen.
    *   *Regime BULL:* Normale Allokation.
    *   *Regime BEAR:* Das Basis-Kapital für Long-Trades in Aktien wird um bis zu 50 % gekürzt. Das System forciert stattdessen Absicherungen (Gold, Anleihen) oder Short-Derivate.
*   **Volatility Sizing (ATR-Sizing):**
    Die Positionsgröße berechnet sich anhand der annualisierten 30-Tage-Volatilität. Hochvolatile Assets (Kryptos, Hebel, Meme-Stocks) erhalten automatisch einen Pufferfaktor (z.B. `0.3x` bis `0.5x`), während extrem schwankungsarme Werte (Staatsanleihen) höher gewichtet werden (`1.5x`).

---

## 4. Die Depot-Spezifischen Strategien & Ausstiege

### A. ⚡ Daytrader-Depot (Intraday / Momentum / High Leverage)
*   **Fokus:** Kurzfristige Echtzeit-Ausbrüche (1-Minuten Spikes) und Reversals.
*   **Instrumente:** Hauptsächlich Knock-Out Turbos (Hebel 2x bis 30x, dynamisch berechnet nach Ausbruchsstärke) oder Direkt-Aktien.
*   **Exits:** 
    *   Strikter Stop-Loss von `-2%` (auf Aktien) oder `-25%` (auf Derivate).
    *   **EOD Derisking:** Nach 21:00 Uhr werden alle im Gewinn liegenden Positionen vor Handelsschluss (Overnight-Risk) glattgestellt.

### B. 🚀 Kurzfristiges Trading-Depot (Swing / Squeezes / Tage–Wochen)
*   **Fokus:** Smart-Money Flow, Put/Call-Ratios (PCR), Gamma-Squeezes und Social Media Sentiment.
*   **Scaling Out (Teilverkäufe):** Bei **+25 % Profit** werden automatisch 50 % der Position verkauft. Der Rest läuft als "Free Ride" weiter.
*   **Exits:** Ratchet Trailing-Stops (ab +8 % auf Breakeven+3 % gezogen, ab +18 % engmaschig bei 6 % unter dem Peak). Fällt der Alpha-Score unter 42, erfolgt ein unplanmäßiger *Thesen-Ausstieg*.

### C. 📈 Mittelfristiges Trend- & Growth-Depot (1–6 Monate)
*   **Fokus:** Trendfolge starker Wachstumsunternehmen, KI-Leader und Momentum-Werte, die die 50-Tage-Linie verteidigen.
*   **Scaling Out (Teilverkäufe):** Bei **+35 % Profit** werden 50 % der Gewinne gesichert.
*   **Opportunitäts-Tausch (Rotation):** "Dead Money" (Titel, die stagnieren und über 20 Alpha-Punkte hinter neuen Ausbrüchen liegen) wird rigoros ausgetauscht.
*   **Exits:** Dynamischer Trailing-Stop mit 8 % Toleranz unter dem bisherigen Höchststand (ab 20 % Profit).

### D. 🏛️ Langfristiges Investment-Depot (Jahre / Quality & Hedge)
*   **Fokus:** Krisenfeste Burggraben-Unternehmen (Piotroski F-Score), Gold und Kern-Kryptos.
*   **Instrumente:** Aktien, Absicherungs-ETFs und bei extrem starken Signalen (Score > 90) Bonus-Zertifikate (z.B. +14 % Rendite bei -25 % Risikopuffer).
*   **Exits:** Kein klassischer Stop-Loss, sondern purely "Qualitäts-Ausstiege". Ein Verkauf erfolgt nur, wenn die fundamentale Bilanz-Qualität (Forensic Score) unter 45 von 100 fällt.

---

## 5. Automatisierung (CI/CD)
Das gesamte System agiert zu 100 % autonom:
*   Ein **GitHub Actions Cronjob** triggert die Skripte kontinuierlich.
*   Die KI aktualisiert Preise, checkt Stops/Regimes, führt das Tribunal aus und committet die Ergebnisse in Form von JSON/SQLite direkt zurück in den `main` Branch.
*   Am Abend (bzw. Wochenende) generiert das `KI-Lerntagebuch` einen menschlich lesbaren Retrospektive-Bericht über Fehler und Erfolge.
