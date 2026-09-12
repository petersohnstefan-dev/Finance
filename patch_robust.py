import sys

with open('src/ai_journal.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the model initialization in __init__
old_init = """    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Find an available model
            model_name = 'gemini-1.5-flash'
            try:
                available = [m.name for m in genai.list_models()]
                if 'models/gemini-1.5-flash' in available:
                    model_name = 'gemini-1.5-flash'
                elif 'models/gemini-1.5-flash-latest' in available:
                    model_name = 'gemini-1.5-flash-latest'
                elif 'models/gemini-1.5-pro-latest' in available:
                    model_name = 'gemini-1.5-pro-latest'
                elif 'models/gemini-pro' in available:
                    model_name = 'gemini-pro'
            except:
                pass
            if '1.5' in model_name:
                self.model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
            else:
                self.model = genai.GenerativeModel(model_name)"""

new_init = """    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)"""

content = content.replace(old_init, new_init)


# Update generate_daily_retrospective
old_gen = """        response = self.model.generate_content(prompt)
        try:
            res_json = json.loads(response.text.strip().removeprefix('```json').removesuffix('```').strip())
        except:"""

new_gen = """        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-pro', 'gemini-1.5-pro-latest', 'gemini-pro']
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
            raise Exception(f"Alle Modelle fehlgeschlagen. Letzter Fehler: {last_err}")
            
        try:
            res_json = json.loads(response.text.strip().removeprefix('```json').removesuffix('```').strip())
        except:"""

content = content.replace(old_gen, new_gen)

with open('src/ai_journal.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ai_journal.py to try multiple models.")

