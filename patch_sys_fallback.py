import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_loop = """                            if '1.5' not in m_name:
                                model = genai.GenerativeModel(m_name)
                            else:
                                model = genai.GenerativeModel(m_name, system_instruction=sys_prompt)
                            
                            gemini_messages = []
                            for m in st.session_state.chat_messages:
                                r = "model" if m["role"] == "assistant" else "user"
                                gemini_messages.append({"role": r, "parts": [m["content"]]})
                            
                            response = model.generate_content(gemini_messages, stream=True)"""

new_loop = """                            if '1.5' not in m_name:
                                model = genai.GenerativeModel(m_name)
                            else:
                                model = genai.GenerativeModel(m_name, system_instruction=sys_prompt)
                            
                            gemini_messages = []
                            for i, m in enumerate(st.session_state.chat_messages):
                                r = "model" if m["role"] == "assistant" else "user"
                                content = m["content"]
                                
                                # Wenn es ein altes Modell (gemini-pro) ist, hängen wir den sys_prompt heimlich 
                                # an die allerletzte User-Nachricht an, da es system_instruction nicht unterstützt.
                                if '1.5' not in m_name and i == len(st.session_state.chat_messages) - 1 and r == "user":
                                    content = f"SYSTEM-KONTEXT (Nutze diese Daten ZWINGEND für deine Antwort, ignoriere dein altes Wissen falls es abweicht! HEUTE IST DER 29.08.2026!):\\n{sys_prompt}\\n\\nBENUTZERFRAGE:\\n{content}"
                                    
                                gemini_messages.append({"role": r, "parts": [content]})
                            
                            response = model.generate_content(gemini_messages, stream=True)"""

content = content.replace(old_loop, new_loop)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched app.py to pass sys_prompt to older gemini models.")
