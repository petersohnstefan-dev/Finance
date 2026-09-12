import io

legend_screener = """        with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Legende)"):
            st.markdown("Hier findest du eine detaillierte Erklärung der Metriken und wie du sie interpretieren solltest:")
            l_col1, l_col2 = st.columns(2)
            with l_col1:
                st.markdown('''
                - **Gesamt-Score (0-100)**: Die Gesamtbewertung der KI (Charttechnik + Fundamentaldaten). 
                  - *> 70*: **Sehr gut**. Starker Buy-Kandidat.
                  - *< 40*: **Schlecht**. Warnsignal, oft im Abwärtstrend.
                - **Trend / M. (Trend & Momentum)**: Misst die Stärke des aktuellen Trends (0-100).
                  - *> 70*: **Gut**. Die Aktie ist in einem starken Aufwärtstrend (RSI, MACD, Gleitende Durchschnitte positiv).
                  - *> 90*: **Achtung**, eventuell überkauft (Rücksetzer möglich).
                  - *< 30*: **Bärisch**. Starker Abwärtstrend.
                - **Val. / Fund. / Inst.** (Value, Fundamental, Institutionell): 
                  - *Value*: Bewertungs-Score. Ein hoher Wert (>70) ist **gut** (günstige Bewertung, z.B. niedriges KGV). 
                  - *Fundamental*: Unternehmensgesundheit (hoher F-Score = starke Bilanz).
                  - *Inst. (Smart Money)*: Große Adressen kaufen. Hoch = **gut**.
                - **KGV (Kurs-Gewinn-Verhältnis)**: Zeigt an, wie oft der Jahresgewinn im Kurs steckt. Niedrig (z.B. < 15) ist historisch gesehen **günstig / gut**.
                - **RSI (Relative Strength Index)**: Misst Überhitzung. 
                  - *< 30*: **Überverkauft** (Rebound-Chance, "günstiger" Einstieg). 
                  - *> 70*: **Überkauft** (Gefahr eines Rücksetzers).
                ''')
            with l_col2:
                st.markdown('''
                - **Vol-Spike (Volumen-Faktor)**: Wie viel höher ist das aktuelle Volumen im Vergleich zum 20-Tage-Schnitt.
                  - *> 1.5x bis 2.0x*: **Sehr gut (beim Ausbruch)**. Institutionelle Anleger kaufen. Ausbrüche ohne Volumen brechen oft ab.
                  - *< 1.0x*: Geringes Interesse.
                - **Short Float (%)**: Anteil der Aktien, die von Bären leerverkauft wurden. 
                  - *> 15%*: **Hohes Short-Squeeze-Risiko/-Potenzial**. Zwingt Bären bei steigenden Kursen zum Nachkaufen (massiver Preisschub nach oben möglich).
                - **Days to Cover (Short Ratio)**: Dauer in Tagen, die Bären bei normalem Volumen bräuchten, um ihre Wetten zu schließen. *> 5 Tage* = Schwer eindeckbar für Bären (Squeeze sehr explosiv).
                - **Ziel % (Analysten)**: Das durchschnittliche Kurspotenzial auf 12 Monate laut Profi-Analysten. 
                  - *Positive Werte*: **Gut** (Analysten erwarten Kursgewinne).
                  - *Hinweis*: Analysten hinken heißen Momentum-Trends oft hinterher.
                - **Katalysator (Ausbruchs-Radar)**: Der Grund für einen plötzlichen Anstieg (z.B. "Earnings Beat", "Zulassung"). Ist fundamentaler Treibstoff für den Ausbruch.
                ''')
"""

legend_realtime = """
    with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Echtzeit-Radar)"):
        st.markdown("Hier findest du eine Erklärung der Echtzeit-Metriken:")
        st.markdown('''
        - **Live-Preis**: Der letzte getickte Kurs.
        - **1-Minuten-Sprung (%)**: Kursänderung in den letzten 60 Sekunden.
          - *> +1.5%*: **Extrem starker** Kaufdruck (oft Ausbruch oder Squeeze). 
          - *Darauf achten*: Solche Spikes ziehen schnell "FOMO" (Fear of Missing Out) an. Nicht blind reinspringen, sondern prüfen, ob der Sprung an einem charttechnischen Ausbruchslevel passiert.
        - **Dringlichkeit (⚡ HOCH)**: Zeigt an, dass der Sprung außergewöhnlich schnell war und sofortige Aufmerksamkeit erfordert.
        - **KI-Meldung & Signal**: Die Schlussfolgerung der KI.
          - *Z.B. "Volumen-Schock!"*: Sehr **gutes** Signal für einen Ausbruch, da hier offensichtlich große Orders (Institutionen) platziert wurden.
        ''')
"""

legend_smartmoney = """
    with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Smart-Money & Makro)"):
        st.markdown('''
        - **Optionen-Fluss (Options Flow)**: Zeigt an, wohin das große Geld (Hedgefonds) fließt. 
          - *Put/Call Ratio < 1.0*: **Bullisch** (Mehr Calls als Puts).
          - *Net Premium (Call)*: Positiv = Millionen-Beträge setzen auf steigende Kurse.
        - **Dark Pools**: Außerbörsliche Handelsplätze für Großinvestoren. 
          - *DIX (Dark Index)*: Hoch = Großinvestoren sammeln heimlich Aktien auf (Bullisch).
        - **Gamma Exposure (GEX)**: Positionierung der Market Maker.
          - *Positiv*: Dämpft Schwankungen (geringe Volatilität).
          - *Negativ*: Verstärkt Schwankungen (Risiko für schnelle Crashs oder Short Squeezes).
        - **BaFin Leerverkäufer**: Offizielle Netto-Leerverkaufspositionen in EU-Aktien.
          - *> 5%*: Massiv geshortet. Ein überraschend gutes Quartalsergebnis kann einen starken "Short-Squeeze" auslösen (schnell steigende Kurse).
        - **COT-Daten (Commitments of Traders)**: Wöchentlicher Bericht über die Positionierung im Terminmarkt.
          - *Commercials*: Die "echten" Absicherer (oft Anti-Indikator zu Trends).
          - *Non-Commercials (Hedgefonds)*: Wenn sie massiv Long sind = Starker Trend oder gefährliche Überhitzung.
        - **MVRV Z-Score (Krypto)**: Bewertungsmaßstab für Bitcoin.
          - *> 7*: Überbewertet / Blase (Rot).
          - *< 0*: Unterbewertet / Bodenbildung (Grün, historisch extrem gute Kaufchance).
        ''')
"""

legend_whale = """
    with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Whale- & Insider-Radar)"):
        st.markdown('''
        - **13F Filings (Whale-Radar)**: Gesetzlich vorgeschriebene Quartalsberichte großer US-Hedgefonds und Investmentbanken (Assets > 100 Mio. $).
          - *Neu-Kauf / Erhöhung*: **Bullisch**. Ein Super-Investor (wie Warren Buffett oder Ray Dalio) hat eine große Position aufgebaut.
          - *Darauf achten*: Die Daten sind bis zu 45 Tage alt, zeigen aber langfristige Überzeugungen.
        - **US-Senatoren & Kongress-Trades**: Zeigt die (meist sehr profitablen) Aktiengeschäfte amerikanischer Politiker.
          - *Auffälliger Kauf*: Politiker sitzen oft in Ausschüssen und haben Vorab-Wissen über Gesetzesänderungen oder Rüstungsaufträge. Ein Kauf vor einer Ankündigung ist ein starkes **(Insider-)Signal**.
        - **Directors Dealings (Insider-Trades)**: Vorstände und Aufsichtsräte kaufen oder verkaufen Aktien der eigenen Firma.
          - *Kauf*: **Sehr Bullisch**. "Es gibt viele Gründe für Insider, eine Aktie zu verkaufen, aber nur einen, sie zu kaufen: Sie denken, der Preis wird steigen." (Peter Lynch).
          - *Verkauf*: Nicht zwingend bärisch (oft Steuergründe oder Optionen-Ausübung), es sei denn, es handelt sich um massive, geplante Abverkäufe vor schlechten News.
        - **Signal-Stärke**: 
          - *🚀 STRONG BUY*: Massiver, unüblicher Insider-Kauf.
          - *⚠️ SELL*: Starkes Abverkauf-Signal.
        ''')
"""

legend_makro = """
    with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Makro & News)"):
        st.markdown('''
        - **Fed (Federal Reserve) / EZB (Europäische Zentralbank)**: Steuern den Leitzins.
        - **Leitzins / Interest Rates**:
          - *Zinssenkung*: **Bullisch** für Aktien (Geld wird billiger, Kredite günstiger).
          - *Zinserhöhung*: **Bärisch** (Geld wird teurer, Anlagen wie Anleihen werden attraktiver als Aktien).
        - **Inflation (CPI/VPI)**: Verbraucherpreise.
          - *Fällt*: Gut für den Aktienmarkt (Zinssenkungen rücken näher).
          - *Steigt*: Schlecht (Gefahr von längeren, höheren Zinsen).
        - **Dot-Plot (Fed)**: Die offizielle Prognose der Fed-Mitglieder, wohin die Zinsen in den nächsten Jahren fallen oder steigen werden.
        ''')
"""

legend_ficc = """
    with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Rohstoffe, Anleihen & Devisen)"):
        st.markdown('''
        - **Anleihen-Rendite (Yields, z.B. 10-Jahre US-Bonds)**: Verzinsung von Staatsanleihen. 
          - *Steigende Renditen*: Oft **bärisch** für Aktien (besonders Tech-Aktien), da festverzinsliche Anlagen als "risikolose Alternative" attraktiver werden.
          - *Fallende Renditen*: Oft **bullisch** für Aktien.
        - **Invertierte Zinskurve (Inverted Yield Curve)**: Die kurzfristigen Zinsen (z.B. 2-Jahre) sind höher als die langfristigen (z.B. 10-Jahre). 
          - *Interpretation*: Historisch einer der sichersten Indikatoren für eine kommende **Rezession**.
        - **High-Yield Spreads (Junk Bonds)**: Die Risikoprämie (Zinsaufschlag), den Unternehmen mit schlechter Bonität zahlen müssen.
          - *Steigende Spreads*: Die Märkte haben Angst, Kreditausfälle drohen (Bärisch).
          - *Fallende Spreads*: Risikobereitschaft hoch, keine Panik (Bullisch).
        - **DXY (US Dollar Index)**: Stärke des Dollars im Vergleich zu anderen Währungen (Euro, Yen, etc.).
          - *Steigender Dollar*: Oft ein Gegenwind für US-Exportunternehmen und Rohstoffe.
        - **Carry Trade (z.B. Yen)**: Investoren leihen sich günstig Geld in Japan (0% Zinsen) und kaufen damit US-Aktien. 
          - *Gefahr*: Steigt der Yen plötzlich stark an, platzen diese Wetten, was zu massiven Aktienverkäufen führt ("Crash").
        ''')
"""

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def replace_between(start_str, end_str, new_content, lines):
    start_idx, end_idx = -1, -1
    for i, l in enumerate(lines):
        if start_str in l:
            start_idx = i
            break
    for i in range(start_idx, len(lines)):
        if end_str in lines[i]:
            end_idx = i
            break
    if start_idx != -1 and end_idx != -1:
        lines = lines[:start_idx] + [new_content + '\n'] + lines[end_idx+1:]
    return lines

def insert_before(marker, content, lines):
    for i, l in enumerate(lines):
        if marker in l:
            return lines[:i] + [content + '\n'] + lines[i:]
    return lines

# 1. Replace Screener Legend
lines = replace_between('with st.expander("📚 Legende zu den Spalten"):', 'st.info("💡 **Tipp**: Wähle links', legend_screener, lines)

# 2. Insert Realtime Radar
lines = insert_before('# MODE 4: SMART-MONEY & MAKRO-RADAR', legend_realtime, lines)

# 3. Insert Smart Money
lines = insert_before('# MODE 4: WHALE- & INSIDER-RADAR', legend_smartmoney, lines)

# 4. Insert Whale
lines = insert_before('# MODE 4: MAKRO-KLIMA, ZENTRALBANKEN & QUALITÄTSMEDIEN', legend_whale, lines)

# 5. Insert Makro
lines = insert_before('# MODE: COMMODITIES, PRECIOUS METALS, OIL & FOREX', legend_makro, lines)

# 6. Insert FICC
lines = insert_before('# MODE 5: MUSTERDEPOTS & LIVE-PERFORMANCE (3 DEPOTS)', legend_ficc, lines)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    
print("Done!")
