from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import sqlite3
from typing import Optional
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

DB_PATH = "database/events.db"
app = FastAPI(title="AutoHeal Workstation Monitor")

# Ruta al archivo .env
load_dotenv()

# Acceder a las variables de .env
user = os.getenv('USER')
password = os.getenv('PASSWORD')

# Configurar el sistema de autenticación -------------------------
security = HTTPBasic()

def verify(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != user or credentials.password != password:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
#------------------------------------------------------------------
def fetch_latest_events(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, hostname, metric, value, status
        FROM events
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "timestamp": row[0],
            "hostname": row[1],
            "metric": row[2],
            "value": row[3],
            "status": row[4]
        }
        for row in rows
    ]

# Función ara comprobar que la API funciona
@app.get("/")
def root():
    return {"Mensaje": "AutoHeal Monitor API en funcionamiento"}
    
# Función para sacar las últimas 10 métricas
@app.get("/metrics")
def get_metrics(
    type: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = 10,
    credentials: HTTPBasicCredentials = Depends(verify)): # requiere autenticación
    # Construir consulta SQL dinámica
    query = "SELECT timestamp, hostname, metric, value, status FROM events WHERE 1=1"
    params = []

    if type:
        query += " AND metric = ?"
        params.append(type)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    # Ejecutar consulta
    conn = sqlite3.connect("database/events.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # Formatear respuesta
    return [
        {
            "timestamp": row[0],
            "hostname": row[1],
            "metric": row[2],
            "value": row[3],
            "status": row[4]
        }
        for row in rows
    ]

# Función para sacar última métrica de cada tipo
@app.get("/metrics/latest")
def get_latest_metrics(credentials: HTTPBasicCredentials = Depends(verify)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT metric, MAX(timestamp) FROM events GROUP BY metric
    """)
    latest_entries = cursor.fetchall()

    results = []
    for metric, timestamp in latest_entries:
        cursor.execute("""
            SELECT timestamp, hostname, metric, value, status
            FROM events
            WHERE metric = ? AND timestamp = ?
            LIMIT 1
        """, (metric, timestamp))
        row = cursor.fetchone()
        if row:
            results.append({
                "timestamp": row[0],
                "hostname": row[1],
                "metric": row[2],
                "value": row[3],
                "status": row[4]
            })

    conn.close()
    return results

# Función para sacar resumen últimas 24 horas. Cuántos "OK", "WARN" y "CRITICAL"
@app.get("/metrics/summary")
def get_summary(credentials: HTTPBasicCredentials = Depends(verify)):
    # Calcular fecha límite (24h atrás)
    cutoff = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, COUNT(*) FROM events
        WHERE timestamp >= ?
        GROUP BY status
    """, (cutoff,))
    rows = cursor.fetchall()
    conn.close()

    summary = {status: count for status, count in rows}
    return summary

# Función para ver Top 5 procesos por uso de CPU o RAM
@app.get("/metrics/top_processes")
def get_top_processes_endpoint(
    by: Optional[str] = "cpu",
    limit: Optional[int] = 5,
    credentials: HTTPBasicCredentials = Depends(verify)
):
    if by not in ["cpu", "memory"]:
        raise HTTPException(status_code=400, detail="Parámetro 'by' debe ser 'cpu' o 'memory'")

    return get_top_processes(by=by, limit=limit)

# Función comprobar estado puertos 22 y 8443
@app.get("/metrics/ports")
def get_ports_status(credentials: HTTPBasicCredentials = Depends(verify)):
    return {
        "port_22": check_port_status(22),
        "port_8443": check_port_status(8443)
    }

# Función para ver conexiones activas
@app.get("/metrics/connections")
def get_connections(credentials: HTTPBasicCredentials = Depends(verify)):
    return get_active_connections()

# Función para ver cantidad de conexiones activas
@app.get("/metrics/connections/count")
def get_connection_count(credentials: HTTPBasicCredentials = Depends(verify)):
    active = get_active_connections()
    return {"active_connections": len(active)}

# Función recibir eventos estado "CRITICAL"
@app.get("/metrics/alerts")
def get_critical_alerts(credentials: HTTPBasicCredentials = Depends(verify)):
    cutoff = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, hostname, metric, value, status
        FROM events
        WHERE status = 'CRITICAL' AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (cutoff,))
    rows = cursor.fetchall()
    conn.close()

    alerts = [
        {
            "timestamp": row[0],
            "hostname": row[1],
            "metric": row[2],
            "value": row[3],
            "status": row[4]
        }
        for row in rows
    ]
    return alerts

# Función para convertir datos en formato válido para Prometheus
@app.get("/metrics/prometheus", response_class=PlainTextResponse)
def get_prometheus_metrics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener la última métrica por tipo
    cursor.execute("""
        SELECT metric, MAX(timestamp) FROM events GROUP BY metric
    """)
    latest_entries = cursor.fetchall()

    lines = []
    for metric, timestamp in latest_entries:
        cursor.execute("""
            SELECT value FROM events
            WHERE metric = ? AND timestamp = ?
            LIMIT 1
        """, (metric, timestamp))
        row = cursor.fetchone()
        if row:
            value = row[0]
            # Si es una métrica con etiquetas (ej: proceso), puedes añadirlas aquí
            lines.append(f"{metric} {value}")

    conn.close()
    return "\n".join(lines)
