import sys

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_lev = """                    if spike > 3.5:
                        chosen_lev = 30.0
                    elif spike > 2.5:
                        chosen_lev = 10.0
                    elif spike > 1.5:
                        chosen_lev = 5.0
                    elif spike > 0.8:
                        chosen_lev = 2.0
                    else:
                        chosen_lev = 1.0 # Ohne Hebel"""

new_lev = """                    if spike >= 2.0:
                        chosen_lev = 30.0
                    elif spike >= 1.2:
                        chosen_lev = 15.0
                    elif spike >= 0.8:
                        chosen_lev = 10.0
                    elif spike >= 0.5:
                        chosen_lev = 5.0
                    else:
                        chosen_lev = 2.0 # Minimum 2x Hebel für Daytrader"""

if old_lev in content:
    content = content.replace(old_lev, new_lev)
    with open('src/portfolio.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched leverage brackets.")
else:
    print("Could not find old_lev")
