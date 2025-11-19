README - Demo ELK Stack con FastAPI
===================================

Este proyecto es una demostración simple del stack ELK (Elasticsearch, Logstash/Beats, Kibana) usando:
- FastAPI como API básica
- CSV como almacenamiento
- Filebeat para enviar logs de la API a Elasticsearch
- Heartbeat para monitorear disponibilidad
- Kibana para visualizar datos y construir dashboards

La intención es educativa y está simplificada al máximo.

## 1. Estructura del proyecto


├── api/
│   ├── main.py        # FastAPI + logging
│   └── items.csv      # Base de datos simple
├── beats/
│   ├── filebeat.yml   # Configuración Filebeat
│   └── heartbeat.yml  # Configuración Heartbeat
├── docker-compose.yml # Levanta Elasticsearch, Kibana, Beats
└── README.txt         # Este archivo


## 2. Cómo levantar ELK


1. Instala Docker y Docker Compose.
2. Ubícate en la carpeta donde está docker-compose.yml.
3. Ejecuta:

docker compose up -d

4. Verifica que Elasticsearch está arriba:

http://localhost:9200

Deberías ver un JSON básico diciendo "You Know, for Search".

5. Entra a Kibana:

http://localhost:5601

La primera carga puede tardar un poco.

## 3. Cómo correr la API


1. Instala dependencias:

pip install fastapi uvicorn pandas

2. Corre la API:

uvicorn api.main:app --reload

3. La API estará disponible en:

http://localhost:8000

4. Endpoints útiles:
- GET /items → lista los items
- POST /items?name=algo → agrega un item
- DELETE /items/{id} → elimina un item

Los logs se generan automáticamente en:
logs/api.log

## 4. Cómo validar que Filebeat funciona

Filebeat recoge logs de:
logs/api.log

Para ver si está enviando logs con éxito:

docker logs filebeat

En Kibana:
1. Ve a “Analytics → Discover”.
2. Crea un Data View:
   Nombre: filebeat-*
   Timestamp: @timestamp

Ahora deberías ver los logs de la API entrando en tiempo real.


## 5. Cómo validar que Heartbeat funciona


Heartbeat monitorea:
http://host.docker.internal:8000

Para revisar si funciona:

docker logs heartbeat

En Kibana:
1. Ve a Stack Monitoring
2. Revisa la sección Heartbeat (Uptime)

## 6. Crear un Dashboard en Kibana

1. Entra a:
Analytics → Dashboard

2. Crea visualizaciones usando índices:
- filebeat-* (logs)
- heartbeat-* (uptime, latencia)

Ejemplos simples:
- Conteo de requests por minuto
- Estado Up/Down de la API
- Latencia promedio
- Top endpoints por frecuencia

3. Toma una captura de pantalla del dashboard final (requisito del proyecto).

## 7. Generar el archivo.log requerido


La API ya genera logs automáticamente.

Para generar 50+ logs:
1. Haz varias llamadas:
   GET http://localhost:8000/items
   POST http://localhost:8000/items?name=test
2. Revisa logs/api.log
3. Copia el archivo a tu entrega.


## 8. Arquitectura resumida (para tu informe)

API (FastAPI)
→ genera logs en logs/api.log

Filebeat
→ lee logs/api.log
→ envía a Elasticsearch

Heartbeat
→ revisa cada X segundos si la API responde
→ envía estado + latencia a Elasticsearch

Elasticsearch
→ almacena logs y métricas

Kibana
→ visualiza en Dashboard
→ permite analizar logs, uptime y métricas

## 9. Cómo limpiar todo

docker compose down -v
rm -rf logs/*
rm -rf elasticsearch-data