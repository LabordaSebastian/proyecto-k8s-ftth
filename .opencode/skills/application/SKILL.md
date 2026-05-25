---
name: application
description: "Use for application code changes: Flask backend endpoints, Python dependencies, Dockerfiles, Nginx config, health checks, API contracts, environment variables, requirements.txt, Dockerfile optimization. Trigger keywords: app, application, backend, frontend, flask, nginx, python, endpoint, api, dockerfile, requirements.txt, dependency, code, source, src, health check, status, redis connection."
---

# Application Agent — Conocimiento de Código Fuente

Carga el conocimiento de dominio leyendo los archivos fuente de Gemini:

```bash
# Lee las convenciones de código del proyecto
read .gemini/skills/application-agent/artifacts/app_skill.md

# Lee el protocolo de operación del agente
read .gemini/skills/application-agent/artifacts/agent_protocol.md
```

El contenido de esos archivos es la fuente de verdad actualizada. Esto incluye:

- **Mapa del código fuente**: estructura de `src/backend/` y `src/frontend/`
- **Backend**: app.py con Flask + Redis, endpoints existentes, patrones de código
- **Patrones obligatorios**: variables de entorno con `os.getenv`, respuestas `jsonify`, error handling try/except
- **Dependencias Python**: `Flask==3.0.0`, `redis==5.0.1`, reglas para agregar nuevas
- **Dockerfile**: imagen `python:3.9-alpine`, orden de capas, optimización de caché
- **Frontend**: ConfigMap montado como volumen, Dockerfile mínimo con `nginx:alpine`
- **Contrato de API**: endpoint `/status` con campos `status`, `message`, `ftth_network`
- **Variables de entorno**: `REDIS_HOST` con default `ftth-redis-service`
