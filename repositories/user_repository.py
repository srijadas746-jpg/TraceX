from typing import Optional, List
from database.db import get_db
from models.user import User

class UserRepository:
    def __init__(self, db_conn=None):
        self._db = db_conn

    def _get_connection(self):
        return self._db if self._db is not None else get_db()

    def get_by_id(self, user_id: int) -> Optional[User]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE id = ?;", (user_id,))
        row = cursor.fetchone()
        return User.from_row(row) if row else None

    def get_by_username(self, username: str) -> Optional[User]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE username = ?;", (username,))
        row = cursor.fetchone()
        return User.from_row(row) if row else None

    def list_all(self) -> List[User]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User ORDER BY id ASC;")
        rows = cursor.fetchall()
        return [User.from_row(r) for r in rows]

    def create(self, username: str, password_hash: str, role: str) -> User:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO User (username, password_hash, role) VALUES (?, ?, ?);",
            (username, password_hash, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return self.get_by_id(user_id)
