import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_state_init = """    if "nav_app_mode" not in st.session_state:
        st.session_state["nav_app_mode"] = "🏆 Markt-Screener & Top-Rankings\""""

new_state_init = """    if "nav_app_mode" not in st.session_state:
        # Load mode from URL query parameters if available
        qp_mode = st.query_params.get("mode")
        if qp_mode:
            st.session_state["nav_app_mode"] = qp_mode
        else:
            st.session_state["nav_app_mode"] = "🏆 Markt-Screener & Top-Rankings\""""

content = content.replace(old_state_init, new_state_init)

old_state_update = """    if app_mode != st.session_state["nav_app_mode"]:
        st.session_state["nav_app_mode"] = app_mode
        st.rerun()"""

new_state_update = """    if app_mode != st.session_state["nav_app_mode"]:
        st.session_state["nav_app_mode"] = app_mode
        # Update URL so user can refresh without losing their place
        st.query_params["mode"] = app_mode
        st.rerun()"""

content = content.replace(old_state_update, new_state_update)

# Also fix the jump to Einzelaktien analysis
old_jump = """st.session_state["nav_app_mode"] = "🔍 Einzelaktien-Tiefenanalyse\""""
new_jump = """st.session_state["nav_app_mode"] = "🔍 Einzelaktien-Tiefenanalyse"
        st.query_params["mode"] = "🔍 Einzelaktien-Tiefenanalyse\""""
content = content.replace(old_jump, new_jump)


with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected URL query parameter state persistence.")
