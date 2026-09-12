import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix the Radio Menu StreamlitAPIException
old_radio = """    if "nav_app_mode" not in st.session_state:
        st.session_state["nav_app_mode"] = "🏆 Markt-Screener & Top-Rankings"

    app_mode = st.radio(
        "Hauptmenü",
        [
            "🏆 Markt-Screener & Top-Rankings", 
            "🚨 Ausbruchs- & Katalysator-Radar",
            "⚡ Echtzeit-Intraday-Radar (Live-Ticks)",
            "🔮 Smart-Money & Makro-Radar (6 Module)",
            "🐋 Whale- & Insider-Radar",
            "🌐 Makro-Klima, Zentralbanken & News",
            "🪙 Rohstoffe, Anleihen, Zinsen & Devisen (FICC)",
            "💼 Musterdepots & Live-Performance (4x 10.000 €)",
            "🔍 Einzelaktien-Tiefenanalyse"
        ],
        key="nav_app_mode",
        label_visibility="collapsed"
    )"""

new_radio = """    if "nav_app_mode" not in st.session_state:
        st.session_state["nav_app_mode"] = "🏆 Markt-Screener & Top-Rankings"

    menu_opts = [
        "🏆 Markt-Screener & Top-Rankings", 
        "🚨 Ausbruchs- & Katalysator-Radar",
        "⚡ Echtzeit-Intraday-Radar (Live-Ticks)",
        "🔮 Smart-Money & Makro-Radar (6 Module)",
        "🐋 Whale- & Insider-Radar",
        "🌐 Makro-Klima, Zentralbanken & News",
        "🪙 Rohstoffe, Anleihen, Zinsen & Devisen (FICC)",
        "💼 Musterdepots & Live-Performance (4x 10.000 €)",
        "🔍 Einzelaktien-Tiefenanalyse"
    ]
    
    current_idx = menu_opts.index(st.session_state["nav_app_mode"]) if st.session_state["nav_app_mode"] in menu_opts else 0

    app_mode = st.radio(
        "Hauptmenü",
        menu_opts,
        index=current_idx,
        label_visibility="collapsed"
    )
    
    if app_mode != st.session_state["nav_app_mode"]:
        st.session_state["nav_app_mode"] = app_mode
        st.rerun()"""

content = content.replace(old_radio, new_radio)

# 2. Fix the WKN issue in the Markt-Screener mode
old_n_cols = """            display_df.columns = [
                "Ticker", "Name", "Kurs", "Währung",
                "Gesamt", "Kurz", "Lang", "Short %",
                "Ziel %", "RSI", "KGV", "Handlungsempfehlung"
            ]"""

new_n_cols = """            display_df["symbol"] = display_df["symbol"].apply(lambda s: get_wkn(s))
            display_df.columns = [
                "WKN", "Name", "Kurs", "Währung",
                "Gesamt", "Kurz", "Lang", "Short %",
                "Ziel %", "RSI", "KGV", "Handlungsempfehlung"
            ]"""
content = content.replace(old_n_cols, new_n_cols)

# And fix col_cfg for the normal mode
old_col_cfg_n = """                "Ticker": st.column_config.TextColumn("Ticker", help="Börsenkürzel der Aktie (z. B. MRNA, SDF.DE)"),
                "Name": st.column_config.TextColumn("Name", help="Name des Unternehmens"),
                "Kurs": st.column_config.TextColumn("Kurs", help="Aktueller Kurs"),
                "Währung": st.column_config.TextColumn("Währung", help="Handelswährung"),
                "Gesamt": st.column_config.NumberColumn("Gesamt-Score", help="Gesamtbewertung der KI (Charttechnik + Fundamentaldaten)"),"""

new_col_cfg_n = """                "WKN": st.column_config.TextColumn("WKN", help="Wertpapierkennnummer der Aktie (z. B. 710000)"),
                "Name": st.column_config.TextColumn("Name", help="Name des Unternehmens"),
                "Kurs": st.column_config.TextColumn("Kurs", help="Aktueller Kurs"),
                "Währung": st.column_config.TextColumn("Währung", help="Handelswährung"),
                "Gesamt": st.column_config.NumberColumn("Gesamt-Score", help="Gesamtbewertung der KI (Charttechnik + Fundamentaldaten)"),"""

content = content.replace(old_col_cfg_n, new_col_cfg_n)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied fixes to app.py")
