import sys
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
lines[456] = '            st.query_params["mode"] = "🔍 Einzelaktien-Tiefenanalyse"\n'
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
