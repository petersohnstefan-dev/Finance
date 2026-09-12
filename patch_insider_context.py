import codecs
import re

# 1. Update insider_whale_tracker.py to use caching
with codecs.open('src/insider_whale_tracker.py', 'r', 'utf8') as f:
    insider_content = f.read()

if 'import streamlit as st' not in insider_content:
    insider_content = 'import streamlit as st\n' + insider_content

insider_content = insider_content.replace(
    '    @staticmethod\n    def get_live_insider_transactions() -> pd.DataFrame:',
    '    @staticmethod\n    @st.cache_data(ttl=600)\n    def get_live_insider_transactions() -> pd.DataFrame:'
)

with codecs.open('src/insider_whale_tracker.py', 'w', 'utf8') as f:
    f.write(insider_content)


# 2. Update app.py to inject insider data into sys_prompt
with codecs.open('app.py', 'r', 'utf8') as f:
    app_content = f.read()

injection_code = '''
                    try:
                        from src.insider_whale_tracker import LiveInsiderWhaleTracker
                        insider_df = LiveInsiderWhaleTracker.get_live_insider_transactions()
                        if not insider_df.empty:
                            sys_prompt += "\\n\\nLIVE INSIDER TRANSAKTIONEN (SEC Form 4):\\n"
                            sys_prompt += insider_df.to_string(index=False) + "\\n"
                    except Exception as e:
                        pass
'''

# Find the spot right after commodities intel is added
pattern = r'(sys_prompt \+= f"- Silberpreis: \$\{pm_data\[\'silver_price\'\]:\.2f\}\\n".*?except Exception as e:\n                        pass)'
match = re.search(pattern, app_content, flags=re.DOTALL)
if match:
    app_content = app_content[:match.end()] + injection_code + app_content[match.end():]
else:
    print("Could not find injection point in app.py")

with codecs.open('app.py', 'w', 'utf8') as f:
    f.write(app_content)
    
print("Patched both files successfully")
