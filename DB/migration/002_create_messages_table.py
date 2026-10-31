import sqlite3
import os

DB_PATH = os.path.join("DB", "database.db")
def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        role TEXT NOT NULL,          -- user / assistant / system
        content TEXT NOT NULL,       -- texte du message
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(conversation_id) REFERENCES conversations(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Messages table created successfully.")
migrate()

# system : Tu es un assistant Smart House (Message spécial utilisé pour le prompting).
# user : Allume la lumière.
# assistant : Lumière allumée.