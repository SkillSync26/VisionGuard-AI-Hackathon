import sqlite3
from datetime import datetime
from .config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        object_class TEXT NOT NULL,
        confidence REAL NOT NULL,
        source TEXT NOT NULL,
        object_count INTEGER DEFAULT 1,
        track_id INTEGER,
        alert_status TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        alert_type TEXT NOT NULL,
        message TEXT NOT NULL,
        severity TEXT DEFAULT 'warning'
    );
    """)
    conn.commit()
    conn.close()

def add_detection(object_class, confidence, source, object_count=1,
                   track_id=None, alert_status=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO detections
        (timestamp, object_class, confidence, source, object_count, track_id, alert_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(timespec="seconds"),
        object_class, float(confidence), source, int(object_count),
        track_id, alert_status
    ))
    conn.commit()
    conn.close()

def add_alert(alert_type, message, severity="warning"):
    conn = get_connection()
    conn.execute("""
        INSERT INTO alerts (timestamp, alert_type, message, severity)
        VALUES (?, ?, ?, ?)
    """, (
        datetime.now().isoformat(timespec="seconds"),
        alert_type, message, severity
    ))
    conn.commit()
    conn.close()

def get_detections(limit=500, object_type=None, source=None, date=None):
    conn = get_connection()
    query = "SELECT * FROM detections WHERE 1=1"
    params = []
    if object_type:
        query += " AND object_class = ?"
        params.append(object_type)
    if source:
        query += " AND source = ?"
        params.append(source)
    if date:
        query += " AND timestamp LIKE ?"
        params.append(f"{date}%")
    query += " ORDER BY id DESC LIMIT ?"
    params.append(int(limit))
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_alerts(limit=200):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (int(limit),)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_statistics():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
    classes = conn.execute("""
        SELECT object_class, COUNT(*) AS count
        FROM detections
        GROUP BY object_class
        ORDER BY count DESC
    """).fetchall()
    sources = conn.execute("""
        SELECT source, COUNT(*) AS count
        FROM detections
        GROUP BY source
        ORDER BY count DESC
    """).fetchall()
    avg_conf = conn.execute(
        "SELECT COALESCE(AVG(confidence), 0) FROM detections"
    ).fetchone()[0]
    alerts = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    conn.close()

    return {
        "total_detections": total,
        "average_confidence": round(float(avg_conf), 4),
        "total_alerts": alerts,
        "by_class": [{"class": r["object_class"], "count": r["count"]} for r in classes],
        "by_source": [{"source": r["source"], "count": r["count"]} for r in sources],
    }

def clear_history():
    conn = get_connection()
    conn.execute("DELETE FROM detections")
    conn.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()
