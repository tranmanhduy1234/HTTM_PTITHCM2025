from db.db import get_connection

def insert_weight(user_id: int, dataset_id: int = None, storage_url: str = None, is_currently_use: bool = False):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO Weight (userID, datasetID, storageURL, isCurrentlyUse, createdAt)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (user_id, dataset_id, storage_url, int(is_currently_use)))
        conn.commit()
        weight_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return weight_id


def get_weights_by_user(user_id: int):
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT ID as id, userID, datasetID, storageURL, isCurrentlyUse, createdAt
            FROM Weight
            WHERE userID = ?
            ORDER BY createdAt DESC
        """, (user_id,))
        rows = cur.fetchall()
        return [dict(zip([c[0] for c in cur.description], row)) for row in rows]


def get_current_weight(user_id: int):
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT ID as id, userID, datasetID, storageURL, isCurrentlyUse, createdAt
            FROM Weight
            WHERE userID = ? AND isCurrentlyUse = 1
            LIMIT 1
        """, (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(zip([c[0] for c in cur.description], row))


def update_current_weight(user_id: int, weight_id: int):
    with get_connection() as conn:
        conn.execute("""
            UPDATE Weight
            SET isCurrentlyUse = 0
            WHERE userID = ?
        """, (user_id,))
        
        # Bật weight mới
        conn.execute("""
            UPDATE Weight
            SET isCurrentlyUse = 1
            WHERE ID = ? AND userID = ?
        """, (weight_id, user_id))
        conn.commit()


def delete_weight(weight_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM Weight WHERE ID = ?", (weight_id,))
        conn.commit()


def get_weight_by_id(weight_id: int):
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT ID as id, userID, datasetID, storageURL, isCurrentlyUse, createdAt
            FROM Weight
            WHERE ID = ?
        """, (weight_id,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(zip([c[0] for c in cur.description], row))
