import sys
import datetime

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

today = datetime.datetime.now().strftime('%d.%m.%Y')
content = content.replace('Vermeide Floskeln."', f'Vermeide Floskeln. HEUTE IST DER {today}."')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched sys_prompt with dynamic date.')
