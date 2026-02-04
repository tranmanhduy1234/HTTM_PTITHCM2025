# repository/user_repo.py
from db.db import get_connection
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# repository/user_repo.py
from db.db import get_connection

def get_user_by_id(user_id: int):
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT ID as id, userName, email, createdAt, isActive
            FROM User
            WHERE ID = ?
        """, (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(row) 

def username_exists(username: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute("SELECT 1 FROM User WHERE userName = ?", (username,))
        return cur.fetchone() is not None


def email_exists(email: str) -> bool:
    if not email:
        return False
    with get_connection() as conn:
        cur = conn.execute("SELECT 1 FROM User WHERE email = ?", (email,))
        return cur.fetchone() is not None


def insert_user(full_name: str, username: str, password_hash: str, email: str, phone: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO User (userName, email, createdAt, isActive, password)
            VALUES (?, ?, datetime('now'), 1, ?)
        """, (username.strip(), email.strip() if email else None, password_hash))
        conn.commit()
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return user_id


def get_user_by_credentials(username: str, password_hash: str):
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT ID, userName, email, createdAt, isActive
            FROM User
            WHERE userName = ? AND password = ?
        """, (username, password_hash))
        return cur.fetchone()
    
def get_user_by_username(username: str):
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT ID as id, userName, email, createdAt, isActive, password
            FROM User
            WHERE userName = ?
        """, (username,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(zip([c[0] for c in cur.description], row))
