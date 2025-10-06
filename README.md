# 🛠️ AutoHeal Workstation Monitor (BETA - En desarrollo)

Sistema ligero de monitorización y respuesta automática para estaciones de trabajo Linux.

## 🎯 Objetivo

Detectar eventos críticos en el sistema (uso excesivo de recursos, servicios caídos, etc.) y ejecutar acciones correctivas automáticamente, mejorando la observabilidad y resiliencia del entorno.

## 🚀 Funcionalidades

- Monitorización de CPU, RAM, disco, procesos y servicios clave.
- Exportación de métricas vía HTTP para Prometheus.
- Dashboard en Grafana para visualización.
- Respuesta automática ante eventos críticos.
- Registro estructurado de eventos en base de datos.
- Instalación automatizada vía `setup.sh`.

## 📁 Estructura del Proyecto
autoheal-workstation-monitor/
├── README.md 
├── LICENSE
├── .gitignore 
├── setup.sh                  # Script de instalación
├── requirements.txt          # Dependencias Python
├── monitor/
│   ├── __init__.py
│   ├── collector.py          # Recolecta métricas del sistema
│   ├── responder.py **(ausente)**          # Ejecuta acciones correctivas
│   ├── exporter.py           # Expone métricas vía HTTP
│   └── logger.py **(ausente)**             # Logging estructurado
├── tests/
│   ├── test_collector.py **(ausente)**
│   ├── test_responder.py **(ausente)**
│   └── test_exporter.py **(ausente)**
├── database/
│   └── events.db             # SQLite (puede generarse en runtime)
├── dashboard/ **(ausente)**
│   └── grafana.json          # Configuración de panel
└── docs/
    └── architecture.md       # Diseño del sistema

## 📦 Instalación

```bash
git clone https://github.com/Fran-SQL/autoheal-workstation-monitor.git
cd autoheal-workstation-monitor
bash setup.sh

# testing
