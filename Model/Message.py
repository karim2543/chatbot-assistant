import sqlite3
import os
from DB.connection import connect, transaction

# --- PROJECT ROOT ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT_DIR, "DB", "database.db")

class Message:
    TABLE_NAME = "messages"

    def __init__(self, conversation_id, role, content, message_id=None, created_at=None):
        self.id = message_id
        self.conversation_id = conversation_id
        self.role = role  # user / assistant / system
        self.content = content
        self.created_at = created_at

    # --- DATABASE CONNECTION ---
    @staticmethod
    def _connect():
        return connect(DB_PATH)

    # --- CRUD METHODS ---
    def save(self):
        with transaction(DB_PATH) as conn:
            cursor = conn.cursor()
            if self.id:
                cursor.execute(f"""
                    UPDATE {self.TABLE_NAME}
                    SET conversation_id=?, role=?, content=?
                    WHERE id=?
                """, (self.conversation_id, self.role, self.content, self.id))
            else:
                cursor.execute(f"""
                    INSERT INTO {self.TABLE_NAME} (conversation_id, role, content)
                    VALUES (?, ?, ?)
                """, (self.conversation_id, self.role, self.content))
                self.id = cursor.lastrowid

    @classmethod
    def get(cls, message_id):
        conn = cls._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, conversation_id, role, content, created_at
            FROM {cls.TABLE_NAME} WHERE id=?
        """, (message_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return cls(conversation_id=row[1], role=row[2], content=row[3], message_id=row[0], created_at=row[4])
        return None

    @classmethod
    def get_by_conversation(cls, conversation_id):
        conn = cls._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, conversation_id, role, content, created_at
            FROM {cls.TABLE_NAME} WHERE conversation_id=?
            ORDER BY id ASC
        """, (conversation_id,))
        rows = cursor.fetchall()
        conn.close()
        return [cls(conversation_id=row[1], role=row[2], content=row[3], message_id=row[0], created_at=row[4]) for row in rows]

    @staticmethod
    def all():
        conn = Message._connect()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, conversation_id, role, content, created_at "
            f"FROM {Message.TABLE_NAME} ORDER BY id ASC"
        )
        rows = cursor.fetchall()
        conn.close()
        return [Message(conversation_id=row[1], role=row[2], content=row[3], message_id=row[0], created_at=row[4]) for row in rows]

    def delete(self):
        if self.id:
            with transaction(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id=?", (self.id,))
            self.id = None

    # --- REPRESENTATION ---
    def __repr__(self):
        return f"<Message id={self.id} conversation_id={self.conversation_id} role='{self.role}' content='{self.content[:30]}'>"