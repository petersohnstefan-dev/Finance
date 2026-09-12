import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_bot = """                        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-pro', 'gemini-1.5-pro-latest', 'gemini-pro']
                        response = None
                        last_err = None
                        
                        for m_name in models_to_try:
                            try:
                                if m_name == 'gemini-pro':
                                    model = genai.GenerativeModel(m_name)
                                else:
                                    model = genai.GenerativeModel(m_name, system_instruction=sys_prompt)
                                
                                gemini_messages = []
                                for m in st.session_state.chat_history:
                                    r = "model" if m["role"] == "assistant" else "user"
                                    gemini_messages.append({"role": r, "parts": [m["content"]]})
                                
                                response = model.generate_content(gemini_messages, stream=True)
                                break
                            except Exception as e:
                                last_err = e
                                response = None
                                
                        if not response:
                            st.error(f"Fehler: Kein passendes Modell gefunden. Letzter Fehler: {last_err}")
                            st.stop()"""

new_bot = """                        response = None
                        last_err = None
                        
                        try:
                            available_models = []
                            for m in genai.list_models():
                                if 'generateContent' in m.supported_generation_methods:
                                    available_models.append(m.name)
                        except Exception as e:
                            st.error(f"Konnte Modell-Liste nicht abrufen. API-Key ungültig? Fehler: {e}")
                            st.stop()
                            
                        if not available_models:
                            st.error("Dein API-Key hat Zugriff auf 0 Modelle, die Text generieren können.")
                            st.stop()
                            
                        available_models.sort(key=lambda x: '1.5' in x, reverse=True)
                        
                        for m_name in available_models:
                            try:
                                if '1.5' not in m_name:
                                    model = genai.GenerativeModel(m_name)
                                else:
                                    model = genai.GenerativeModel(m_name, system_instruction=sys_prompt)
                                
                                gemini_messages = []
                                for m in st.session_state.chat_history:
                                    r = "model" if m["role"] == "assistant" else "user"
                                    gemini_messages.append({"role": r, "parts": [m["content"]]})
                                
                                response = model.generate_content(gemini_messages, stream=True)
                                if response:
                                    break
                            except Exception as e:
                                last_err = e
                                response = None
                                
                        if not response:
                            st.error(f"Fehler bei allen Modellen (versucht: {len(available_models)}). Letzter Fehler: {last_err}")
                            st.stop()"""

content = content.replace(old_bot, new_bot)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched app.py with full dynamic model logic.")
