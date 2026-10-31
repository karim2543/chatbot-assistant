import sqlite3
import os
from DB.connection import connect, transaction

# --- PROJECT ROOT ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT_DIR, "DB", "database.db")

class Conversation:
    TABLE_NAME = "conversations"

    def __init__(self, user_id, title, conversation_id=None, created_at=None):
        self.id = conversation_id
        self.user_id = user_id
        self.title = title
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
                    SET user_id=?, title=?
                    WHERE id=?
                """, (self.user_id, self.title, self.id))
            else:
                cursor.execute(f"""
                    INSERT INTO {self.TABLE_NAME} (user_id, title)
                    VALUES (?, ?)
                """, (self.user_id, self.title))
                self.id = cursor.lastrowid

    @classmethod
    def get(cls, conversation_id):
        conn = cls._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, user_id, title, created_at
            FROM {cls.TABLE_NAME} WHERE id=?
        """, (conversation_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return cls(user_id=row[1], title=row[2], conversation_id=row[0], created_at=row[3])
        return None

    @classmethod
    def get_for_user(cls, conversation_id, user_id):
        conversation = cls.get(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            return None
        return conversation

    @classmethod
    def get_by_user(cls, user_id):
        conn = cls._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, user_id, title, created_at
            FROM {cls.TABLE_NAME} WHERE user_id=?
            ORDER BY id ASC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [cls(user_id=row[1], title=row[2], conversation_id=row[0], created_at=row[3]) for row in rows]

    @classmethod
    def normalize_titles(cls, user_id):
        conversations = cls.get_by_user(user_id)
        with transaction(DB_PATH) as conn:
            conn.executemany(
                f"UPDATE {cls.TABLE_NAME} SET title=? WHERE id=? AND user_id=?",
                [
                    (f"Conversation {index}", conversation.id, user_id)
                    for index, conversation in enumerate(conversations, start=1)
                ],
            )
        for index, conversation in enumerate(conversations, start=1):
            conversation.title = f"Conversation {index}"
        return conversations

    @staticmethod
    def all():
        conn = Conversation._connect()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, user_id, title, created_at "
            f"FROM {Conversation.TABLE_NAME} ORDER BY id ASC"
        )
        rows = cursor.fetchall()
        conn.close()
        return [Conversation(user_id=row[1], title=row[2], conversation_id=row[0], created_at=row[3]) for row in rows]

    def delete(self):
        if self.id:
            with transaction(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM messages WHERE conversation_id=?",
                    (self.id,),
                )
                cursor.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id=?", (self.id,))
            self.id = None

    # --- REPRESENTATION ---
    def __repr__(self):
        return f"<Conversation id={self.id} user_id={self.user_id} title='{self.title}'>"