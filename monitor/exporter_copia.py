from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import sqlite3
from typing import Optional
import os
from dotenv import load_dotenv

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

# Faunción para comprobar que la API funciona
@app.get("/")
def root():
    return {"message": "AutoHeal Monitor API is running"}
