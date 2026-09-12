import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

old_expander = 'with st.expander(f"{log[\'timestamp\']} | {log[\'symbol\']} ({log[\'depot_id\']}) - {icon} {log[\'action\']}"):'
new_expander = 'name_str = log.get("name", "-")\n            with st.expander(f"{log[\'timestamp\']} | {log[\'symbol\']} - {name_str} ({log[\'depot_id\']}) - {icon} {log[\'action\']}"):'

if old_expander in content:
    content = content.replace(old_expander, new_expander)
    with codecs.open('app.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Patched app.py expander")
else:
    print("old_expander not found")
