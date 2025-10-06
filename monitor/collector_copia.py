import psutil
import socket
from datetime import datetime
import sqlite3
import os

DB_PATH = "database/events.db"

# Crear la tabla si no existe
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            hostname TEXT,
            metric TEXT,
            value REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_hostname():
    return socket.gethostname()

def collect_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent
    }

def log_event(metric, value, status="OK"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (timestamp, hostname, metric, value, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        get_hostname(),
        metric,
        value,
        status
    ))
    conn.commit()
    conn.close()

def run():
    metrics = collect_metrics()
    for metric, value in metrics.items():
        status = "OK" if value < 80 else "WARN"  # Umbral simple
        log_event(metric, value, status)

if __name__ == "__main__":
    os.makedirs("database", exist_ok=True) # asegurarse de que la carpeta database/ existe
    init_db()
    run()
