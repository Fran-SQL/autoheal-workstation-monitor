#!/bin/bash

echo "Iniciando instalación de AutoHeal Workstation Monitor..."

# 1. Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then
  echo "Por favor, ejecuta como root (sudo)"
  exit 1
fi

# 2. Actualizar paquetes
apt update && apt upgrade -y

# 3. Instalar dependencias del sistema
apt install -y python3 python3-pip python3-venv sqlite3 curl

# 4. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 5. Instalar dependencias Python
pip install --upgrade pip
pip install -r requirements.txt

# 6. Crear carpeta database si no existe
if [ ! -d "database" ]; then
  echo "Creando carpeta 'database/'..."
  mkdir database
fi

# 7. Crear base de datos si no existe
if [ ! -f database/events.db ]; then
  echo "Creando base de datos..."
  sqlite3 database/events.db < docs/schema.sql
fi

# 8. Crear carpeta docs si no existe
if [ ! -d "docs" ]; then
  echo "Creando carpeta 'docs/'..."
  mkdir docs
fi

# 9. Crear schema.sql si no existe
if [ ! -f "docs/schema.sql" ]; then
  echo "Archivo 'docs/schema.sql' no encontrado. Creando esquema base..."
  cat <<EOF > docs/schema.sql
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    hostname TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    status TEXT NOT NULL
);
EOF
fi

# 10. Mensaje final
echo "Instalación completada. Ejecuta el monitor con: source venv/bin/activate && python monitor/exporter.py"
