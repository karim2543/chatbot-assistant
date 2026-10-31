import sqlite3
import os

DB_PATH = os.path.join("DB", "database.db")
def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assistant_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        temperature REAL DEFAULT 0.5,    -- créativité de l'IA (0=précis, 1=créatif)
        language TEXT DEFAULT 'en',      -- langue de l'assistant
        voice_enabled INTEGER DEFAULT 1, -- 1 = réponses vocales activées, 0 = désactivées
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("Assistant Settings table created successfully.")
migrate()