import sys

with open('src/db.py', 'r', encoding='utf-8') as f:
    content = f.read()

table_sql = """
            # Radar History
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS radar_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detected_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                signal_price REAL NOT NULL,
                score REAL,
                theme TEXT
            );
            ''')
"""

if 'CREATE TABLE IF NOT EXISTS radar_history' not in content:
    content = content.replace(
        "CREATE TABLE IF NOT EXISTS hourly_snapshots", 
        table_sql.strip() + "\n\n            cursor.execute('''\n            CREATE TABLE IF NOT EXISTS hourly_snapshots"
    )

methods_code = """
    def record_radar_signals(self, signals: list):
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._get_conn() as conn:
            cursor = conn.cursor()
            for s in signals:
                cursor.execute('''
                    INSERT INTO radar_history (detected_at, symbol, name, signal_price, score, theme)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (now_str, s.get("symbol"), s.get("name", s.get("symbol")), s.get("price", 0.0), s.get("breakout_score", 0.0), s.get("theme", "")))
            conn.commit()

    def get_recent_radar_signals(self, limit=20):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT detected_at, symbol, name, signal_price, score, theme 
                FROM radar_history 
                ORDER BY detected_at DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            res = []
            for r in rows:
                res.append({
                    "detected_at": r[0],
                    "symbol": r[1],
                    "name": r[2],
                    "signal_price": r[3],
                    "score": r[4],
                    "theme": r[5]
                })
            return res
"""

if 'def record_radar_signals' not in content:
    content += "\n" + methods_code

with open('src/db.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Added radar_history to db.py')

import sqlite3
c = sqlite3.connect('data/portfolio.db')
c.execute("""
CREATE TABLE IF NOT EXISTS radar_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    signal_price REAL NOT NULL,
    score REAL,
    theme TEXT
);
""")
c.commit()
print('Initialized radar_history table in SQLite')
