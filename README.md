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

## 📦 Instalación

```bash
git clone https://github.com/Fran-SQL/autoheal-workstation-monitor.git
cd autoheal-workstation-monitor
bash setup.sh

# testing
