import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_hist = "hist_text = str(b_hist_df.tail(7)['us_10y_yield'].to_dict())"
new_hist = "hist_text = str(b_hist_df.tail(7).set_index('date')['us_10y_yield'].to_dict())"
content = content.replace(old_hist, new_hist)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed date index in FICC prompt.")
