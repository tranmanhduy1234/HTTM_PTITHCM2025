from db.db import get_connection
from datetime import datetime

def insert_frame(drowsy_video_id: int, confidence: float, prediction: bool, image_path: str):
    """Insert a frame into the Frame table (datasetID luôn NULL)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Frame (drowsyVideoID, confidenceScore, modelPrediction, imageURL, datasetID, createdAt)
            VALUES (?, ?, ?, ?, NULL, ?)
        """, (drowsy_video_id, confidence, prediction, image_path, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid

def get_frames_by_video(video_id: int):
    """Retrieve all frames for a given video."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT ID, confidenceScore, modelPrediction, imageURL, createdAt
            FROM Frame
            WHERE drowsyVideoID = ?
            ORDER BY createdAt ASC
        """, (video_id,))
        return cursor.fetchall()

def delete_frames_by_video(video_id: int):
    """Delete all frames for a given video."""
    with get_connection() as conn:
        conn.execute("DELETE FROM Frame WHERE drowsyVideoID = ?", (video_id,))
        conn.commit()

def get_high_confidence_frames(drowsy_video_id: int, threshold: float = 0.7):
    """Lấy các frame có confidenceScore > threshold từ 1 video."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT ID, drowsyVideoID, confidenceScore, modelPrediction, imageURL
            FROM Frame
            WHERE drowsyVideoID = ? AND confidenceScore > ? AND modelPrediction = 1
        """, (drowsy_video_id, threshold))
        return cursor.fetchall()

def insert_frame_to_dataset(frame, dataset_id: int):
    """Chèn frame vào dataset (tạo bản sao của frame với datasetID mới)."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO Frame (drowsyVideoID, confidenceScore, modelPrediction, imageURL, datasetID)
            VALUES (?, ?, ?, ?, ?)
        """, (
            frame["drowsyVideoID"],
            frame["confidenceScore"],
            frame["modelPrediction"],
            frame["imageURL"],
            dataset_id
        ))
        conn.commit()

def get_frames_by_dataset(dataset_id: int):
    """
    Lấy toàn bộ frame thuộc dataset.
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT ID, drowsyVideoID, confidenceScore, modelPrediction, imageURL, createdAt
            FROM Frame
            WHERE datasetID = ?
            ORDER BY createdAt ASC
        """, (dataset_id,))
        return cursor.fetchall()