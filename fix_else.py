import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('\nelse:\n    st.sidebar.subheader("🔍 Aktie auswählen")', '\nelif app_mode == "🔍 Einzelaktien-Tiefenanalyse":\n    st.sidebar.subheader("🔍 Aktie auswählen")')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
