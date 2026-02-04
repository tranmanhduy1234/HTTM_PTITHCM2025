from db.db import get_connection
from datetime import datetime

def get_daily_drowsy_frequency(user_id, days=7):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            SUBSTR(DrowsyVideo.startTime, 1, 8) AS raw_date,
            COUNT(*) AS count
        FROM DrowsyVideo
        JOIN Session ON DrowsyVideo.sessionID = Session.ID
        WHERE Session.userID = ?
        AND raw_date >= strftime('%Y%m%d', datetime('now', ?))
        GROUP BY raw_date
        ORDER BY raw_date ASC
    """

    cursor.execute(query, (user_id, f'-{days} days'))
    rows = cursor.fetchall()

    # Chuyển "20251031" → "2025-10-31"
    result = [
        {'date': f"{r[0][:4]}-{r[0][4:6]}-{r[0][6:8]}", 'count': r[1]}
        for r in rows
    ]
    return result

def get_hourly_drowsy_frequency(user_id: int):
    """
    Trả về tần suất buồn ngủ theo từng giờ trong 24h qua.
    
    Returns:
        List[dict]: [
            { 'hour': '2025-10-31 13:00', 'count': 3 },
            ...
        ]
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT 
                SUBSTR(DrowsyVideo.startTime, 1, 8) || SUBSTR(DrowsyVideo.startTime, 9, 3) AS raw_time,
                SUBSTR(DrowsyVideo.startTime, 1, 8) || ' ' || SUBSTR(DrowsyVideo.startTime, 10, 2) AS hour_key,
                COUNT(*) AS count
            FROM DrowsyVideo
            JOIN Session ON DrowsyVideo.sessionID = Session.ID
            WHERE Session.userID = ?
              AND DrowsyVideo.startTime >= strftime('%Y%m%d_%H%M%S', datetime('now', '-24 hours'))
            GROUP BY hour_key
            ORDER BY hour_key ASC
        """, (user_id,))

        rows = cursor.fetchall()

        # format kết quả cho dễ đọc
        results = []
        for hour_key, count in [(r[1], r[2]) for r in rows]:
            # hour_key = '20251031 21' → '2025-10-31 21:00'
            formatted_hour = f"{hour_key[:4]}-{hour_key[4:6]}-{hour_key[6:8]} {hour_key[9:]}:00"
            results.append({'hour': formatted_hour, 'count': count})
        return results

def get_daily_detail_statistics(user_id: int, days: int = 7):
    """
    Trả về thống kê chi tiết theo ngày:
      - Số video cảnh báo (model detect)
      - Số video người dùng xác nhận (bất kỳ label != NULL)
      - Tổng thời gian lái trong ngày (cộng dồn tất cả session)
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT 
                DATE(Session.startTime) AS date,
                COUNT(DrowsyVideo.ID) AS alert_count,
                SUM(CASE WHEN DrowsyVideo.userChoiceLabel IS NOT NULL THEN 1 ELSE 0 END) AS confirmed_count,
                SUM(
                    CASE 
                        WHEN Session.endTime IS NOT NULL 
                        THEN (julianday(Session.endTime) - julianday(Session.startTime)) * 24 * 60 * 60
                        ELSE 0 
                    END
                ) AS total_seconds
            FROM DrowsyVideo
            JOIN Session ON DrowsyVideo.sessionID = Session.ID
            WHERE Session.userID = ?
              AND Session.startTime >= datetime('now', ?)
            GROUP BY DATE(Session.startTime)
            ORDER BY date DESC
        """, (user_id, f'-{days} days'))

        rows = cursor.fetchall()

        results = []
        for date, alert_count, confirmed_count, total_seconds in rows:
            hours, remainder = divmod(int(total_seconds or 0), 3600)
            minutes = remainder // 60

            results.append({
                "date": datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y"),
                "alert_count": alert_count or 0,
                "confirmed_count": confirmed_count or 0,
                "driving_time": f"{hours}h {minutes}m" if total_seconds else "--"
            })

        return results
