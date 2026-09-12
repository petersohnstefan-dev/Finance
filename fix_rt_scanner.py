import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add cached instantiation at line 35
new_top_code = """# Page Configuration
st.set_page_config(
    page_title="AI Börsen-Entscheidungs-System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_global_rt_scanner():
    return RealTimeBreakoutScanner()

rt_scanner = get_global_rt_scanner()"""

old_top_code = """# Page Configuration
st.set_page_config(
    page_title="AI Börsen-Entscheidungs-System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)"""

content = content.replace(old_top_code, new_top_code)

# 2. Remove the old instantiation at line 538 (now around 547)
old_line = "    rt_scanner = RealTimeBreakoutScanner()\n"
new_line = "    # rt_scanner is now global\n"
content = content.replace(old_line, new_line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected global rt_scanner")
