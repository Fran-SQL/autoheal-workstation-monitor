import psutil
import socket
from datetime import datetime
import sqlite3
import os
import shutil

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

# Devolver el nombre de host de la máquina 
def get_hostname():
    return socket.gethostname()

# Recoger métricas de CPU, RAM y disco
def collect_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent
    }

# Registrar métricas en base de datos SQLite
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

# Función para obtener Top 5 procesos por uso de CPU o RAM
def get_top_processes(by="cpu", limit=5):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu_percent" if by == "cpu" else "memory_percent"
    top = sorted(processes, key=lambda p: p.get(key, 0), reverse=True)[:limit]

    return [
        {
            "pid": p["pid"],
            "name": p["name"],
            key: round(p[key], 2)
        }
        for p in top
    ]

# Función para almacenar procesos si consumen mucha CPU, más de 80%
def detect_high_cpu_processes(threshold=80.0):
    hostname = socket.gethostname()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("database/events.db")
    cursor = conn.cursor()

    for proc in psutil.process_iter(['name', 'cpu_percent']):
        try:
            cpu = proc.info['cpu_percent']
            name = proc.info['name']
            if cpu is not None and cpu > threshold:
                cursor.execute("""
                    INSERT INTO events (timestamp, hostname, metric, value, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (timestamp, hostname, "high_cpu_process", cpu, "CRITICAL"))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    conn.commit()
    conn.close()

# Función para almacenar procesos si consumen mucha RAM, más de 80%
def detect_high_memory_processes(threshold=80.0):
    hostname = socket.gethostname()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("database/events.db")
    cursor = conn.cursor()

    for proc in psutil.process_iter(['name', 'memory_percent']):
        try:
            mem = proc.info['memory_percent']
            name = proc.info['name']
            if mem is not None and mem > threshold:
                cursor.execute("""
                    INSERT INTO events (timestamp, hostname, metric, value, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (timestamp, hostname, "high_memory_process", mem, "CRITICAL"))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    conn.commit()
    conn.close()

# Función para detectar conexiones activas
def get_active_connections(ports=[22, 8443]):
    connections = psutil.net_connections(kind='inet')
    active = []

    for conn in connections:
        if conn.status == 'ESTABLISHED' and conn.laddr.port in ports:
            active.append({
                "local_port": conn.laddr.port,
                "remote_ip": conn.raddr.ip if conn.raddr else None,
                "remote_port": conn.raddr.port if conn.raddr else None,
                "pid": conn.pid
            })

    return active

# Función calcular uso por directorio
def get_directory_usage(path):
    try:
        total, used, free = shutil.disk_usage(path)
        percent_used = round((used / total) * 100, 2)
        return percent_used
    except FileNotFoundError:
        return None

# Para la función de abajo que registra métricas por directorio
def get_directory_usage(path):
    try:
        total, used, free = shutil.disk_usage(path)
        percent_used = round((used / total) * 100, 2)
        return percent_used
    except FileNotFoundError:
        return None

# Función registrar métricas por directorio
def monitor_directories(directories=["/var/log", "/tmp", "/home"]):
    hostname = socket.gethostname()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("database/events.db")
    cursor = conn.cursor()

    for path in directories:
        usage = get_directory_usage(path)
        if usage is not None:
            if usage < 80:
                status = "OK"
            elif usage < 90:
                status = "WARN"
            else:
                status = "CRITICAL"  # ALERTA activada

            metric = f"disk_usage_{path.replace('/', '_')}"
            cursor.execute("""
                INSERT INTO events (timestamp, hostname, metric, value, status)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, hostname, metric, usage, status))

    conn.commit()
    conn.close()


# Función principal
# Pone en marcha monitorización y registros de las métricas
def run():
    metrics = collect_metrics()
    for metric, value in metrics.items():
        status = "OK" if value < 80 else "WARN"  # Umbral "OK" o "WARN"
        log_event(metric, value, status)

    # Detectar procesos que superan el umbral de CPU o RAM
    detect_high_cpu_processes(threshold=80.0)
    detect_high_memory_processes(threshold=80.0)
    check_critical_ports()
    monitor_directories()
    
if __name__ == "__main__":
    os.makedirs("database", exist_ok=True) # asegurarse de que la carpeta database/ existe
    init_db()
    run()
