import sys

with open('src/ai_journal.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_init = """    def __init__(self, api_key: str):
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
            self.model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})"""

# Find the old init
old_init_start = content.find("    def __init__(self, api_key: str):")
old_init_end = content.find("    def get_todays_trades", old_init_start)
if old_init_start != -1 and old_init_end != -1:
    content = content[:old_init_start] + new_init + "\n\n" + content[old_init_end:]
    with open('src/ai_journal.py', 'w', encoding='utf-8') as f:
        f.write(content)
print("Patched ai_journal.py")

# Now patch app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_bot = """                        model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=sys_prompt)"""

new_bot = """                        model_name = 'gemini-1.5-flash'
                        try:
                            available = [m.name for m in genai.list_models()]
                            if 'models/gemini-1.5-flash' in available:
                                model_name = 'gemini-1.5-flash'
                            elif 'models/gemini-1.5-flash-latest' in available:
                                model_name = 'gemini-1.5-flash-latest'
                            elif 'models/gemini-1.5-pro' in available:
                                model_name = 'gemini-1.5-pro'
                            elif 'models/gemini-1.5-pro-latest' in available:
                                model_name = 'gemini-1.5-pro-latest'
                            elif 'models/gemini-pro' in available:
                                model_name = 'gemini-pro'
                        except:
                            pass
                        
                        # Fallback for old gemini-pro which doesn't support system_instruction
                        if model_name == 'gemini-pro':
                            model = genai.GenerativeModel(model_name)
                            # Prepend sys prompt to history
                            if not st.session_state.chat_history:
                                st.session_state.chat_history.append({"role": "user", "content": sys_prompt})
                                st.session_state.chat_history.append({"role": "model", "content": "Verstanden. Ich bin bereit."})
                        else:
                            model = genai.GenerativeModel(model_name, system_instruction=sys_prompt)"""

content = content.replace(old_bot, new_bot)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched app.py")
