import sqlite3
import os

# --- PROJECT ROOT ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT_DIR, "DB", "database.db")

class VoiceMessage:
    TABLE_NAME = "voice_messages"

    def __init__(self, user_id, file_path, message_id=None, created_at=None):
        self.id = message_id
        self.user_id = user_id        # référence vers users.id
        self.file_path = file_path    # chemin du fichier audio
        self.created_at = created_at

    # --- DATABASE CONNECTION ---
    @staticmethod
    def _connect():
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    # --- CRUD METHODS ---
    def save(self):
        conn = self._connect()
        cursor = conn.cursor()
        if self.id:
            cursor.execute(f"""
                UPDATE {self.TABLE_NAME}
                SET user_id=?, file_path=?
                WHERE id=?
            """, (self.user_id, self.file_path, self.id))
        else:
            cursor.execute(f"""
                INSERT INTO {self.TABLE_NAME} (user_id, file_path)
                VALUES (?, ?)
            """, (self.user_id, self.file_path))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    @classmethod
    def get(cls, message_id):
        conn = cls._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, user_id, file_path, created_at
            FROM {cls.TABLE_NAME} WHERE id=?
        """, (message_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return cls(user_id=row[1], file_path=row[2], message_id=row[0], created_at=row[3])
        return None

    @classmethod
    def get_by_user(cls, user_id):
        conn = cls._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, user_id, file_path, created_at
            FROM {cls.TABLE_NAME} WHERE user_id=?
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [cls(user_id=row[1], file_path=row[2], message_id=row[0], created_at=row[3]) for row in rows]

    @staticmethod
    def all():
        conn = VoiceMessage._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, user_id, file_path, created_at FROM {VoiceMessage.TABLE_NAME}")
        rows = cursor.fetchall()
        conn.close()
        return [VoiceMessage(user_id=row[1], file_path=row[2], message_id=row[0], created_at=row[3]) for row in rows]

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
        return f"<VoiceMessage id={self.id} user_id={self.user_id} file_path='{self.file_path}'>"