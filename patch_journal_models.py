import sys

with open('src/ai_journal.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_gen = """        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-pro', 'gemini-1.5-pro-latest', 'gemini-pro']
        response = None
        last_err = None
        
        for m_name in models_to_try:
            try:
                if '1.5' in m_name:
                    temp_model = genai.GenerativeModel(m_name, generation_config={"response_mime_type": "application/json"})
                else:
                    temp_model = genai.GenerativeModel(m_name)
                response = temp_model.generate_content(prompt)
                break
            except Exception as e:
                last_err = e
                response = None
                
        if not response:
            raise Exception(f"Alle Modelle fehlgeschlagen. Letzter Fehler: {last_err}")"""

new_gen = """        response = None
        last_err = None
        
        # Holen aller verfügbaren Modelle dynamisch vom Server
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # m.name ist meistens 'models/gemini-1.5-flash', wir können das direkt übergeben
                    available_models.append(m.name)
        except Exception as e:
            raise Exception(f"Konnte Modell-Liste nicht abrufen. API-Key ungültig? Fehler: {e}")

        if not available_models:
            raise Exception("Dein API-Key hat Zugriff auf 0 Modelle, die Text generieren können.")

        # Wir priorisieren 1.5 Modelle, falls vorhanden
        available_models.sort(key=lambda x: '1.5' in x, reverse=True)

        for m_name in available_models:
            try:
                if '1.5' in m_name:
                    temp_model = genai.GenerativeModel(m_name, generation_config={"response_mime_type": "application/json"})
                else:
                    temp_model = genai.GenerativeModel(m_name)
                response = temp_model.generate_content(prompt)
                if response:
                    break
            except Exception as e:
                last_err = e
                response = None
                
        if not response:
            raise Exception(f"Versuchte {len(available_models)} Modelle (inkl. {available_models[:3]}). Alle schlugen fehl. Letzter Fehler: {last_err}")"""

content = content.replace(old_gen, new_gen)

with open('src/ai_journal.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ai_journal.py for full dynamic model testing.")
