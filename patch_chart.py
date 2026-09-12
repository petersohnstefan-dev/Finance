import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the night filter
old_filter = """            # 🟢 HIER WIRD DIE NACHT GEFILTERT (Kein Handel zwischen 22:00 und 07:00)
            if not eq_df.empty:
                eq_df["hour_check"] = pd.to_datetime(eq_df["date"]).dt.hour
                eq_df = eq_df[(eq_df["hour_check"] >= 7) & (eq_df["hour_check"] <= 22)]"""

new_filter = """            # 🟢 HIER WIRD DIE NACHT GEFILTERT (Kein Handel zwischen 22:00 und 06:00)
            if not eq_df.empty:
                eq_df["hour_check"] = pd.to_datetime(eq_df["date"]).dt.hour
                eq_df = eq_df[(eq_df["hour_check"] >= 6) & (eq_df["hour_check"] <= 22)]"""

content = content.replace(old_filter, new_filter)

# 2. Add update_xaxes(type="category") to fix gaps
old_layout = """            fig_eq.update_layout(
                template="plotly_white",
                height=480,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified"
            )
            fig_eq.update_yaxes(title_text="Euro (€)", row=1, col=1)
            fig_eq.update_yaxes(title_text="P&L (€)", row=2, col=1)
            st.plotly_chart(fig_eq, use_container_width=True)"""

new_layout = """            fig_eq.update_layout(
                template="plotly_white",
                height=480,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified"
            )
            # Nutze Kategorie-Achse, damit fehlende Stunden (Lücken) einfach ignoriert und die Balken zusammengerückt werden
            fig_eq.update_xaxes(type="category", nticks=15)
            
            fig_eq.update_yaxes(title_text="Euro (€)", row=1, col=1)
            fig_eq.update_yaxes(title_text="P&L (€)", row=2, col=1)
            st.plotly_chart(fig_eq, use_container_width=True)"""

content = content.replace(old_layout, new_layout)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched app.py to fix chart gaps.")
