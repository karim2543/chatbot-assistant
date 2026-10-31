import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from DB.connection import connect

# --- PROJECT ROOT ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT_DIR, "DB", "database.db")

class User:
    TABLE_NAME = "user"

    def __init__(self, username, email, password, role='user', user_id=None, created_at=None, hashed=False):
        self.id = user_id
        self.username = username
        self.email = email
        if hashed:
            self.password = password
        else:
            self.password = generate_password_hash(password)
        self.role = role
        self.created_at = created_at

    # --- DATABASE CONNECTION ---
    @staticmethod
    def _connect():
        return connect(DB_PATH)

    # --- CRUD METHODS ---
    def save(self):
        conn = self._connect()
        cursor = conn.cursor()
        if self.id:
            cursor.execute(f"""
                UPDATE {self.TABLE_NAME}
                SET username=?, email=?, password=?, role=?
                WHERE id=?
            """, (self.username, self.email, self.password, self.role, self.id))
        else:
            cursor.execute(f"""
                INSERT INTO {self.TABLE_NAME} (username, email, password, role)
                VALUES (?, ?, ?, ?)
            """, (self.username, self.email, self.password, self.role))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    @classmethod
    def get(cls, user_id):
        conn = cls._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, username, email, password, role, created_at
            FROM {cls.TABLE_NAME} WHERE id=?
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return cls(*row[1:], user_id=row[0], created_at=row[5], hashed=True)
        return None
    @classmethod
    def getByUserName(cls, username):
        conn = cls._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, username, email, password, role, created_at
            FROM {cls.TABLE_NAME} WHERE username=?
        """, (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return cls(
                username=row[1],
                email=row[2],
                password=row[3],
                role=row[4],
                user_id=row[0],
                created_at=row[5],
                hashed=True
            )
        return None

    @staticmethod
    def all():
        conn = User._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, username, email, password, role, created_at FROM {User.TABLE_NAME}")
        rows = cursor.fetchall()
        conn.close()
        return [
            User(
                username=row[1],
                email=row[2],
                password=row[3],
                role=row[4],
                user_id=row[0],
                created_at=row[5],
                hashed=True,
            )
            for row in rows
        ]

    def delete(self):
        if self.id:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id=?", (self.id,))
            conn.commit()
            conn.close()
            self.id = None

    # --- PASSWORD CHECK ---
    def check_password(self, password):
        return check_password_hash(self.password, password)

    # --- REPRESENTATION ---
    def __repr__(self):
        return f"<User id={self.id} username='{self.username}' role='{self.role}'>"
