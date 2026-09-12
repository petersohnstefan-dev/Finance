import sys

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if l.startswith("                        response = None") and lines[i-3].strip() == "pass":
        # It's indented at 24 spaces. It needs to be indented at 20 spaces, outside the except!
        break

# I will just write a script to re-indent the block
# From line containing "response = None" up to "st.stop()"

# We can replace the whole chunk

old_chunk = """                    except:
                        pass
                        

                        response = None
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

new_chunk = """                    except:
                        pass
                        
                    response = None
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

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(old_chunk, new_chunk)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Indentation fixed.")
