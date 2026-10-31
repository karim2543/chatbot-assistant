import sqlite3
import os

DB_PATH = os.path.join("DB", "database.db")
def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS voice_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,          -- référence vers users.id
        file_path TEXT NOT NULL UNIQUE,           -- chemin du fichier audio
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Voice Messages table created successfully.")
migrate()