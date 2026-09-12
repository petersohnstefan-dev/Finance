import sys

with open('src/ai_journal.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_init = """            self.model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})"""

new_init = """            if '1.5' in model_name:
                self.model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
            else:
                self.model = genai.GenerativeModel(model_name)"""

content = content.replace(old_init, new_init)

with open('src/ai_journal.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched fallback json mode.")
