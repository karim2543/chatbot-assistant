import sqlite3
import os

DB_PATH = os.path.join("DB", "database.db")
def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS intents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,           -- nom de l'intent (ex: turn_on_light)
        description TEXT,             -- description de l'intent (ex: Allumer une lumière dans la maison)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("Intents table created successfully.")
migrate()

# Améliorer le NLP / l’IA
# Tu peux entraîner un modèle pour classifier les intents :
# Input : message texte
# Output : intent correspondant