import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_chat_block = """# MODE 9: KI CHATBOT
elif app_mode == "💬 KI-Chatbot (Strategie & Analyse)":
    st.header("💬 KI-Chatbot (Strategie & Analyse)")
    st.markdown("Frage die KI nach Erklärungen zu Trades im Musterdepot, der Entwicklung von Zinsen, Leerverkäufen, Makro-Daten oder Insider-Aktivitäten.")
    
    api_key = ""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", "")
    except:
        pass
        
    if not api_key:
        api_key = st.text_input("OpenAI API Key (wird nicht gespeichert)", type="password")
        
    if not api_key:
        st.warning("Bitte gib einen OpenAI API Key ein oder konfiguriere ihn in den Streamlit Secrets (`.streamlit/secrets.toml`), um den Chat zu nutzen.")
    else:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            if "chat_messages" not in st.session_state:
                st.session_state.chat_messages = [
                    {"role": "assistant", "content": "Hallo! Ich bin dein KI-Trading-Assistent. Frag mich gerne nach den Gründen für bestimmte Musterdepot-Trades, der Entwicklung von Zinsen, Leerverkäufen oder der Makroökonomie!"}
                ]
            
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
            prompt = st.chat_input("Was möchtest du wissen?")
            if prompt:
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                    
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    
                    sys_prompt = "Du bist ein professioneller KI-Trading-Assistent einer hochentwickelten Finanz-App. Erkläre Finanzkonzepte, Zinsentwicklungen, Short-Squeeze-Mechaniken und warum bestimmte Trades in bestimmten Marktsituationen sinnvoll sind. Antworte präzise, auf Deutsch und fachlich fundiert. Vermeide Floskeln."
                    try:
                        import json
                        with open("data/portfolios.json", "r", encoding="utf-8") as f:
                            pf_data = json.load(f)
                        sys_prompt += "\\n\\nHier ist der aktuelle Zustand der Musterdepots und die Transaktionshistorie (Käufe/Verkäufe) als JSON, damit du konkrete Fragen zu ausgeführten Trades beantworten kannst:\\n" + json.dumps(pf_data)
                    except:
                        pass
                        
                    api_messages = [{"role": "system", "content": sys_prompt}] + [
                        {"role": m["role"], "content": m["content"]} for m in st.session_state.chat_messages
                    ]
                    
                    stream = client.chat.completions.create(
                        model="gpt-4o",
                        messages=api_messages,
                        stream=True,
                    )
                    full_response = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                
                st.session_state.chat_messages.append({"role": "assistant", "content": full_response})
                
        except ImportError:
            st.error("Das 'openai' Python-Paket ist nicht installiert. Bitte füge 'openai' zu deiner requirements.txt hinzu.")
        except Exception as e:
            st.error(f"Fehler bei der KI-Anfrage: {e}")"""

new_chat_block = """# MODE 9: KI CHATBOT
elif app_mode == "💬 KI-Chatbot (Strategie & Analyse)":
    st.header("💬 KI-Chatbot (Strategie & Analyse)")
    st.markdown("Frage die KI nach Erklärungen zu Trades im Musterdepot, der Entwicklung von Zinsen, Leerverkäufen, Makro-Daten oder Insider-Aktivitäten.")
    
    api_key = ""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except:
        pass
        
    if not api_key:
        api_key = st.text_input("Google Gemini API Key (wird nicht gespeichert)", type="password")
        
    if not api_key:
        st.warning("Bitte gib einen Gemini API Key ein oder konfiguriere ihn in den Streamlit Secrets (`.streamlit/secrets.toml` als `GEMINI_API_KEY`), um den Chat zu nutzen.")
    else:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            if "chat_messages" not in st.session_state:
                st.session_state.chat_messages = [
                    {"role": "assistant", "content": "Hallo! Ich bin dein KI-Trading-Assistent. Frag mich gerne nach den Gründen für bestimmte Musterdepot-Trades, der Entwicklung von Zinsen, Leerverkäufen oder der Makroökonomie!"}
                ]
            
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
            prompt = st.chat_input("Was möchtest du wissen?")
            if prompt:
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                    
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    
                    sys_prompt = "Du bist ein professioneller KI-Trading-Assistent einer hochentwickelten Finanz-App. Erkläre Finanzkonzepte, Zinsentwicklungen, Short-Squeeze-Mechaniken und warum bestimmte Trades in bestimmten Marktsituationen sinnvoll sind. Antworte präzise, auf Deutsch und fachlich fundiert. Vermeide Floskeln."
                    try:
                        import json
                        with open("data/portfolios.json", "r", encoding="utf-8") as f:
                            pf_data = json.load(f)
                        sys_prompt += "\\n\\nHier ist der aktuelle Zustand der Musterdepots und die Transaktionshistorie (Käufe/Verkäufe) als JSON, damit du konkrete Fragen zu ausgeführten Trades beantworten kannst:\\n" + json.dumps(pf_data)
                    except:
                        pass
                        
                    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=sys_prompt)
                    
                    gemini_messages = []
                    for m in st.session_state.chat_messages:
                        role = "user" if m["role"] == "user" else "model"
                        gemini_messages.append({"role": role, "parts": [m["content"]]})
                    
                    # Call generate_content (streaming)
                    response = model.generate_content(gemini_messages, stream=True)
                    
                    full_response = ""
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                
                st.session_state.chat_messages.append({"role": "assistant", "content": full_response})
                
        except ImportError:
            st.error("Das 'google-generativeai' Python-Paket ist nicht installiert. Bitte überprüfe die requirements.txt.")
        except Exception as e:
            st.error(f"Fehler bei der KI-Anfrage: {e}")"""

if old_chat_block in content:
    content = content.replace(old_chat_block, new_chat_block)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched Chat UI to use Gemini API.")
else:
    print("Could not find old_chat_block")
