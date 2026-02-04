from db.db import get_connection
from datetime import datetime
import sqlite3


def insert_drowsy_video(session_id: int, start_time: datetime, end_time: datetime = None):
    # Định dạng ngày tháng là YYYY-MM-DDTHH:MM:SS
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           INSERT INTO DrowsyVideo (sessionID, startTime, endTime, userChoiceLabel)
                           VALUES (?, ?, ?, NULL)
                           """, (
                               session_id,
                               start_time.isoformat(),
                               end_time.isoformat() if end_time else None
                           ))
            conn.commit()
            return cursor.lastrowid

    except sqlite3.Error as e:
        print(f"❌ Database error when inserting DrowsyVideo: {e}")
        if 'conn' in locals():
            conn.rollback()
        return None

    except Exception as e:
        print(f"⚠️ Unexpected error in insert_drowsy_video: {e}")
        if 'conn' in locals():
            conn.rollback()
        return None


def update_user_choice_by_start_time(end_time: str, user_choice: bool):
    """
    Cập nhật userChoiceLabel trong bảng DrowsyVideo dựa vào startTime.
    
    Args:
        start_time (str): thời gian kết thúc video, định dạng '%Y%m%d_%H%M%S' (ví dụ '20251022_204652')
        user_choice (bool): nhãn người dùng xác nhận (True/False)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           UPDATE DrowsyVideo
                           SET userChoiceLabel = ?
                           WHERE endTime = ?
                           """, (user_choice, end_time))

            conn.commit()

            if cursor.rowcount == 0:
                print(f"⚠️ Không có bản ghi nào có startTime = {end_time}")
            else:
                print(f"✅ Đã cập nhật {cursor.rowcount} bản ghi userChoiceLabel = {user_choice}")

            return cursor.rowcount

    except sqlite3.Error as e:
        print(f"❌ Lỗi database khi cập nhật userChoiceLabel: {e}")
        if 'conn' in locals():
            conn.rollback()
        return 0


def update_user_choice_by_id(id: int, user_choice: bool):
    """
    Cập nhật userChoiceLabel trong bảng DrowsyVideo dựa vào startTime.

    Args:
        start_time (str): thời gian kết thúc video, định dạng '%Y%m%d_%H%M%S' (ví dụ '20251022_204652')
        user_choice (bool): nhãn người dùng xác nhận (True/False)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           UPDATE DrowsyVideo
                           SET userChoiceLabel = ?
                           WHERE ID = ?
                           """, (user_choice, id))

            conn.commit()

            if cursor.rowcount == 0:
                print(f"⚠️ Không có bản ghi nào có ID = {id}")
            else:
                print(f"✅ Đã cập nhật {cursor.rowcount} bản ghi userChoiceLabel = {user_choice}")

            return cursor.rowcount

    except sqlite3.Error as e:
        print(f"❌ Lỗi database khi cập nhật userChoiceLabel: {e}")
        if 'conn' in locals():
            conn.rollback()
        return 0


def create_drowsy_video(session_id: int, start_time: datetime, end_time: datetime):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT INTO DrowsyVideo (sessionID, startTime, isLabel, endTime)
                       VALUES (?, ?, 0, ?)
                       """, (session_id, start_time.format(), end_time))
        conn.commit()
        return cursor.lastrowid


def get_drowsy_video_by_start_time(start_time: str):
    """
    Truy vấn video theo startTime (định dạng 'YYYYMMDD_HHMMSS')
    """
    with get_connection() as conn:
        cursor = conn.execute("""
                              SELECT ID, sessionID, startTime, endTime, userChoiceLabel
                              FROM DrowsyVideo
                              WHERE startTime = ?
                              """, (start_time,))
        return cursor.fetchone()


def get_unlabeled_drowsy_videos_by_user(user_id: int):
    """
    Lấy danh sách các video (DrowsyVideo) của người dùng 
    mà chưa được gán nhãn (userChoiceLabel IS NULL).
    
    Args:
        user_id (int): ID của người dùng.
    
    Returns:
        List[dict]: danh sách video chưa gán nhãn, mỗi phần tử có dạng:
            {
                "id": int,
                "session_id": int,
                "start_time": str,
                "end_time": str
            }
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT DrowsyVideo.ID,
                                  DrowsyVideo.sessionID,
                                  DrowsyVideo.startTime,
                                  DrowsyVideo.endTime
                           FROM DrowsyVideo
                                    JOIN Session ON DrowsyVideo.sessionID = Session.ID
                           WHERE Session.userID = ?
                             AND DrowsyVideo.userChoiceLabel IS NULL
                           ORDER BY DrowsyVideo.startTime DESC
                           """, (user_id,))

            rows = cursor.fetchall()

            results = [
                {
                    "id": row[0],
                    "session_id": row[1],
                    "start_time": row[2],
                    "end_time": row[3]
                }
                for row in rows
            ]
            return results

    except sqlite3.Error as e:
        print(f"❌ Database error in get_unlabeled_drowsy_videos_by_user: {e}")
        return []
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        return []


def get_all_drowsy_videos_by_user(user_id: int):
    """
        Lấy danh sách các video (DrowsyVideo) của người dùng

        Args:
            user_id (int): ID của người dùng.

        Returns:
            List[dict]: danh sách video, mỗi phần tử có dạng:
                {
                    "id": int,
                    "session_id": int,
                    "start_time": str,
                    "end_time": str
                }
        """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT DrowsyVideo.ID,
                                  DrowsyVideo.sessionID,
                                  DrowsyVideo.startTime,
                                  DrowsyVideo.endTime,
                                  DrowsyVideo.userChoiceLabel
                           FROM DrowsyVideo
                                    JOIN Session ON DrowsyVideo.sessionID = Session.ID
                           WHERE Session.userID = ?
                           ORDER BY DrowsyVideo.startTime DESC
                           """, (user_id,))

            rows = cursor.fetchall()

            results = [
                {
                    "id": row[0],
                    "session_id": row[1],
                    "start_time": row[2],
                    "end_time": row[3],
                    "userChoiceLabel": row[4]
                }
                for row in rows
            ]
            return results

    except sqlite3.Error as e:
        print(f"❌ Database error in get_unlabeled_drowsy_videos_by_user: {e}")
        return []
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        return []
