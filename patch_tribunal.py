import codecs

with codecs.open('src/tribunal.py', 'r', 'utf-8') as f:
    content = f.read()

# Update signature
content = content.replace(
    'def _log_to_db(self, symbol, depot_id, bull, bear, judge, action):',
    'def _log_to_db(self, symbol, name, depot_id, bull, bear, judge, action):'
)

# Update INSERT SQL
content = content.replace(
    'INSERT INTO tribunal_logs (timestamp, symbol, depot_id, bull_case, bear_case, judge_decision, action)',
    'INSERT INTO tribunal_logs (timestamp, symbol, name, depot_id, bull_case, bear_case, judge_decision, action)'
)

# Update VALUES
content = content.replace(
    'VALUES (?, ?, ?, ?, ?, ?, ?)',
    'VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
)

# Update tuple
content = content.replace(
    '(now_str, symbol, depot_id, bull, bear, judge, action)',
    '(now_str, symbol, name, depot_id, bull, bear, judge, action)'
)

# Update where _log_to_db is called!
content = content.replace(
    'self._log_to_db(sym, depot_id, bull_case, bear_case, judge_reasoning, action)',
    'self._log_to_db(sym, candidate.get("name", sym), depot_id, bull_case, bear_case, judge_reasoning, action)'
)

with codecs.open('src/tribunal.py', 'w', 'utf-8') as f:
    f.write(content)

print('Patched tribunal.py')
