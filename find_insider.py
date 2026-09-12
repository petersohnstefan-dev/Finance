import codecs
with codecs.open('app.py', 'r', 'utf8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'Insider' in line and 'CEO' in line:
        out = ''.join(lines[i-2:i+30])
        with codecs.open('temp_app_insider.txt', 'w', 'utf8') as f2:
            f2.write(out)
        break
