import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_menu = """    menu_opts = [
        "🏆 Markt-Screener & Top-Rankings", 
        "🚨 Ausbruchs- & Katalysator-Radar",
        "⚡ Echtzeit-Intraday-Radar (Live-Ticks)",
        "🔮 Smart-Money & Makro-Radar (6 Module)",
        "🐋 Whale- & Insider-Radar",
        "🌐 Makro-Klima, Zentralbanken & News",
        "🪙 Rohstoffe, Anleihen, Zinsen & Devisen (FICC)",
        "💼 Musterdepots & Live-Performance (4x 10.000 €)",
        "🔍 Einzelaktien-Tiefenanalyse",
        "💬 KI-Chatbot (Strategie & Analyse)"
    ]"""

new_menu = """    menu_opts = [
        "🏆 Markt-Screener & Top-Rankings", 
        "🚨 Ausbruchs- & Katalysator-Radar",
        "⚡ Echtzeit-Intraday-Radar (Live-Ticks)",
        "🔮 Smart-Money & Makro-Radar (6 Module)",
        "🐋 Whale- & Insider-Radar",
        "🌐 Makro-Klima, Zentralbanken & News",
        "🪙 Rohstoffe, Anleihen, Zinsen & Devisen (FICC)",
        "💼 Musterdepots & Live-Performance (4x 10.000 €)",
        "🔍 Einzelaktien-Tiefenanalyse",
        "💬 KI-Chatbot (Strategie & Analyse)",
        "🧠 KI-Lerntagebuch (Retrospektive)"
    ]"""

content = content.replace(old_menu, new_menu)

journal_block = """
# MODE 10: KI LERNTAGEBUCH
elif app_mode == "🧠 KI-Lerntagebuch (Retrospektive)":
    st.header("🧠 KI-Lerntagebuch (Daily Retrospectives)")
    st.markdown("Hier analysiert die KI jeden Abend ihre eigenen Trades, zieht Schlüsse aus Fehlern und bewertet verpasste Signale.")
    
    api_key = ""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except:
        pass
        
    col1, col2 = st.columns([2,1])
    with col1:
        if not api_key:
            api_key = st.text_input("Google Gemini API Key (wird nicht gespeichert)", type="password")
            
    with col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Heutige Retrospektive jetzt generieren (EOD)"):
            if not api_key:
                st.error("Bitte gib zuerst deinen Gemini API Key ein.")
            else:
                with st.spinner("KI analysiert die heutigen Trades und verpassten Signale..."):
                    from src.ai_journal import AIJournalEngine
                    engine = AIJournalEngine(api_key)
                    try:
                        engine.generate_daily_retrospective()
                        st.success("Tagebucheintrag erfolgreich generiert!")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler bei der Generierung: {e}")

    st.markdown("---")
    
    from src.ai_journal import AIJournalEngine
    journals = AIJournalEngine.get_all_journals()
    
    if not journals:
        st.info("Noch keine Tagebucheinträge vorhanden. Klicke auf 'Heutige Retrospektive jetzt generieren', um den ersten Eintrag zu erstellen!")
    else:
        for j in journals:
            with st.expander(f"📅 Handelstag: {j['date']} | Win-Rate: {j['win_rate']}%", expanded=(j == journals[0])):
                c1, c2, c3 = st.columns(3)
                c1.metric("Win-Rate", f"{j['win_rate']}%")
                c2.metric("Bester Trade", j['best_trade'] or "-")
                c3.metric("Schlechtester Trade", j['worst_trade'] or "-")
                
                st.markdown("### 🧐 Reflexion (Ausgeführte Trades)")
                st.info(j['reflection'])
                
                st.markdown("### 👻 Verpasste Chancen (Nicht gehandelte Signale)")
                st.warning(j['missed_opportunities'])
                
                st.markdown("### 💡 Lektion für den nächsten Tag")
                st.success(j['lesson'])
"""

content += journal_block

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Injected journal block.")
