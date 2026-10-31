import sqlite3
import os

# --- PROJECT ROOT ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT_DIR, "DB", "database.db")

class AssistantSettings:
    TABLE_NAME = "assistant_settings"

    def __init__(self, temperature=0.5, language='en', voice_enabled=1, setting_id=None, created_at=None):
        self.id = setting_id
        self.temperature = temperature        # créativité de l'IA
        self.language = language              # langue de l'assistant
        self.voice_enabled = voice_enabled    # 1 = vocal activé, 0 = désactivé
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
                SET temperature=?, language=?, voice_enabled=?
                WHERE id=?
            """, (self.temperature, self.language, self.voice_enabled, self.id))
        else:
            cursor.execute(f"""
                INSERT INTO {self.TABLE_NAME} (temperature, language, voice_enabled)
                VALUES (?, ?, ?)
            """, (self.temperature, self.language, self.voice_enabled))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    @classmethod
    def get(cls, setting_id):
        conn = cls._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, temperature, language, voice_enabled, created_at
            FROM {cls.TABLE_NAME} WHERE id=?
        """, (setting_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return cls(temperature=row[1], language=row[2], voice_enabled=row[3],
                       setting_id=row[0], created_at=row[4])
        return None

    @staticmethod
    def all():
        conn = AssistantSettings._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, temperature, language, voice_enabled, created_at FROM {AssistantSettings.TABLE_NAME}")
        rows = cursor.fetchall()
        conn.close()
        return [AssistantSettings(temperature=row[1], language=row[2], voice_enabled=row[3],
                                  setting_id=row[0], created_at=row[4]) for row in rows]

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
        return (f"<AssistantSettings id={self.id} temperature={self.temperature} "
                f"language='{self.language}' voice_enabled={self.voice_enabled}>")