import sqlite3
import os

# --- PROJECT ROOT ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT_DIR, "DB", "database.db")

class Intent:
    TABLE_NAME = "intents"

    def __init__(self, name, description=None, intent_id=None, created_at=None):
        self.id = intent_id
        self.name = name                 # nom de l'intent (ex: turn_on_light)
        self.description = description   # description ou usage
        self.created_at = created_at

    # --- DATABASE CONNECTION ---
    @staticmethod
    def _connect():
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        return conn

    # --- CRUD METHODS ---
    def save(self):
        conn = self._connect()
        cursor = conn.cursor()
        if self.id:
            cursor.execute(f"""
                UPDATE {self.TABLE_NAME}
                SET name=?, description=?
                WHERE id=?
            """, (self.name, self.description, self.id))
        else:
            cursor.execute(f"""
                INSERT INTO {self.TABLE_NAME} (name, description)
                VALUES (?, ?)
            """, (self.name, self.description))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    @classmethod
    def get(cls, intent_id):
        conn = cls._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, name, description, created_at
            FROM {cls.TABLE_NAME} WHERE id=?
        """, (intent_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return cls(name=row[1], description=row[2], intent_id=row[0], created_at=row[3])
        return None

    @staticmethod
    def all():
        conn = Intent._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, name, description, created_at FROM {Intent.TABLE_NAME}")
        rows = cursor.fetchall()
        conn.close()
        return [Intent(name=row[1], description=row[2], intent_id=row[0], created_at=row[3]) for row in rows]

    def delete(self):
        if self.id:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id=?", (self.id,))
            conn.commit()
            conn.close()
            self.id = None

    # --- REPRESENTATION ---
    def __repr__(self):
        return f"<Intent id={self.id} name='{self.name}' description='{self.description}'>"