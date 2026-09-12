import sys

with open('src/ai_journal.py', 'r', encoding='utf-8') as f:
    content = f.read()

migration_code = """
def _migrate_ai_journal_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Check if 'mode' column exists
    cursor.execute("PRAGMA table_info(ai_journal)")
    columns = [info[1] for info in cursor.fetchall()]
    if "mode" not in columns and "win_rate" in columns:
        try:
            cursor.execute('ALTER TABLE ai_journal ADD COLUMN mode TEXT DEFAULT "daily"')
            cursor.execute('ALTER TABLE ai_journal ADD COLUMN param_updates TEXT DEFAULT "{}"')
            conn.commit()
        except Exception as e:
            pass
    conn.close()

# Run migration on import
_migrate_ai_journal_db()
"""

# Find a good place to insert this, right after the get_berlin_now function
target = """def get_berlin_now() -> datetime.datetime:
    try:
        return datetime.datetime.now(BERLIN_TZ)
    except Exception:
        return datetime.datetime.utcnow() + datetime.timedelta(hours=2)"""

content = content.replace(target, target + "\n" + migration_code)

with open('src/ai_journal.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ai_journal.py with auto-migration.")
