from db.db import get_connection
from datetime import datetime

def create_session(user_id: int):
    """Create a new session for a user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Session (userID, startTime)
            VALUES (?, ?)
        """, (user_id, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid

def end_session(session_id: int):
    """End a session."""
    with get_connection() as conn:
        conn.execute("""
            UPDATE Session SET endTime = ? WHERE ID = ?
        """, (datetime.now().isoformat(), session_id))
        conn.commit()

def get_latest_session(user_id: int):
    """Retrieve the latest session for a user."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM Session
            WHERE userID = ?
            ORDER BY startTime DESC
            LIMIT 1
        """, (user_id,))
        return cursor.fetchone()