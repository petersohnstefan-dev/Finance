import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_ui = """    col1, col2 = st.columns([2,1])
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
                st.success(j['lesson'])"""

new_ui = """    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        if not api_key:
            api_key = st.text_input("Google Gemini API Key (wird nicht gespeichert)", type="password")
            
    with col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Tages-Retrospektive (EOD)"):
            if not api_key:
                st.error("Bitte gib zuerst deinen API Key ein.")
            else:
                with st.spinner("Analysiere heutigen Tag..."):
                    from src.ai_journal import AIJournalEngine
                    engine = AIJournalEngine(api_key)
                    try:
                        engine.generate_retrospective(mode="daily")
                        st.success("Tages-Eintrag generiert!")
                        import time; time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")
                        
    with col3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("📅 Wochen-Retrospektive (Freitag)"):
            if not api_key:
                st.error("Bitte gib zuerst deinen API Key ein.")
            else:
                with st.spinner("Analysiere die letzten 7 Tage..."):
                    from src.ai_journal import AIJournalEngine
                    engine = AIJournalEngine(api_key)
                    try:
                        engine.generate_retrospective(mode="weekly")
                        st.success("Wochen-Eintrag generiert!")
                        import time; time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")

    st.markdown("---")
    
    from src.ai_journal import AIJournalEngine
    journals = AIJournalEngine.get_all_journals()
    
    if not journals:
        st.info("Noch keine Tagebucheinträge vorhanden. Klicke auf 'Tages-Retrospektive', um den ersten Eintrag zu erstellen!")
    else:
        for j in journals:
            mode_icon = "📅 Woche" if j.get("mode") == "weekly" else "📆 Tag"
            with st.expander(f"{mode_icon}: {j['date']} | Win-Rate: {j['win_rate']}%", expanded=(j == journals[0])):
                c1, c2, c3 = st.columns(3)
                c1.metric("Win-Rate", f"{j['win_rate']}%")
                c2.metric("Bester Trade", j['best_trade'] or "-")
                c3.metric("Schlechtester Trade", j['worst_trade'] or "-")
                
                st.markdown("### 🧐 Reflexion")
                st.info(j['reflection'])
                
                if j.get("mode") != "weekly":
                    st.markdown("### 👻 Verpasste Chancen (Nicht gehandelte Signale)")
                    st.warning(j['missed_opportunities'])
                
                st.markdown("### 💡 Lektion für die Zukunft")
                st.success(j['lesson'])
                
                # Check for param updates
                param_updates = j.get("param_updates")
                if param_updates and param_updates != "{}" and param_updates != "null":
                    st.markdown("### ⚙️ Automatisch angepasste Strategie-Parameter")
                    st.code(param_updates, language="json")"""

content = content.replace(old_ui, new_ui)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched app.py with weekly journal UI.")
