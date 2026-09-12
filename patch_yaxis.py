import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_yaxes = 'fig_eq.update_yaxes(title_text="Euro (€)", row=1, col=1)'
new_yaxes = """            # Berechne dynamische Y-Achsen-Grenzen, damit fill='tozeroy' den Chart nicht plattdrückt
            try:
                min_val = eq_df["total_value"].min()
                max_val = eq_df["total_value"].max()
                
                # Falls die Benchmarks da sind, beachte auch deren min/max grob (wir nehmen +/- 10% zur Sicherheit)
                padding = max((max_val - min_val) * 0.5, 300) # Mindestens 300 Euro Abstand nach oben und unten
                
                # Hard-Cap für den Start (z.B. +/- 1000 vom Baseline)
                y_bottom = min(min_val, 10000.0) - padding
                y_top = max(max_val, 10000.0) + padding
                
                fig_eq.update_yaxes(title_text="Euro (€)", range=[y_bottom, y_top], row=1, col=1)
            except:
                fig_eq.update_yaxes(title_text="Euro (€)", row=1, col=1)"""

content = content.replace(old_yaxes, new_yaxes)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched y-axis range in app.py")
