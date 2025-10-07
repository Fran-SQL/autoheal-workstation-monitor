#!/bin/bash

# Ruta absoluta al script collector.py
SCRIPT_PATH="$(realpath ./collector.py)"
LOG_PATH="$HOME/autoheal_logs/collector.log"

# Crear carpeta de logs si no existe
mkdir -p "$(dirname "$LOG_PATH")"

# Línea que queremos añadir al crontab
CRON_LINE="*/5 * * * * /usr/bin/python3 $SCRIPT_PATH >> $LOG_PATH 2>&1"

# Verificar si ya existe
(crontab -l 2>/dev/null | grep -F "$SCRIPT_PATH") && {
    echo "Ya existe una entrada en tu crontab para collector.py. No se añadió otra."
    exit 0
}

# Añadir al crontab
(crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -

echo "Recolección automática activada cada 5 minutos."
echo "Logs: $LOG_PATH"
