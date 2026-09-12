import sqlite3
import os

def alter_db():
    db_path = 'data/portfolio.db'
    if not os.path.exists(db_path):
        print("DB nicht gefunden.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if fees column exists
    cursor.execute('PRAGMA table_info(trades);')
    cols = [col[1] for col in cursor.fetchall()]
    
    if 'fees' not in cols:
        print("Füge Spalte 'fees' zu 'trades' hinzu...")
        cursor.execute("ALTER TABLE trades ADD COLUMN fees REAL DEFAULT 0.0;")
        conn.commit()
    else:
        print("Spalte 'fees' existiert bereits.")
        
    conn.close()

if __name__ == '__main__':
    alter_db()
