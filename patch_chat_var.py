import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("st.session_state.chat_history", "st.session_state.chat_messages")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched chat_history to chat_messages.")
