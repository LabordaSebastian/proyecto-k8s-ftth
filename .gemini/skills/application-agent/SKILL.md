---
name: application
description: "Use for application code changes: Flask backend endpoints, Python dependencies, Dockerfiles, Nginx config, health checks, API contracts, environment variables, requirements.txt, Dockerfile optimization. Trigger keywords: app, application, backend, frontend, flask, nginx, python, endpoint, api, dockerfile, requirements.txt, dependency, code, source, src, health check, status, redis connection."
---

# Application Agent — Conocimiento de Código Fuente

Carga el conocimiento de dominio leyendo los archivos fuente de Gemini:

```bash
# Lee las convenciones de código del proyecto

# Lee el protocolo de operación del agente
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


## Content from app_skill.md

# Application Agent — Knowledge Base (app_skill.md)

> Conocimiento específico del proyecto para el Application Agent.
> Leer junto con `agent_protocol.md` antes de operar.

---

## Mapa del Código Fuente

```
src/
├── backend/
│   ├── app.py            ← Aplicación Flask. Único archivo de lógica.
│   ├── requirements.txt  ← 2 dependencias: Flask==3.0.0, redis==5.0.1
│   └── Dockerfile        ← python:3.9-alpine, EXPOSE 5000, CMD python app.py
└── frontend/
    └── Dockerfile        ← nginx:alpine (el HTML viene del ConfigMap, no de src/)
```

### Nota importante sobre el Frontend

El HTML del dashboard **no está en `src/frontend/`** — está en el ConfigMap `ftth-dashboard-html` en `k8s/02-storage/frontend-configmap.yaml`. Esto es intencional (separación de configuración y código). Para cambiar el dashboard, se edita el ConfigMap, no un archivo en `src/`.

---

## Backend — Patrones de Código

### Estructura actual de `app.py`

```python
from flask import Flask, jsonify
import redis
import os

app = Flask(__name__)

# Conexión a Redis usando DNS interno de K8s
redis_host = os.getenv("REDIS_HOST", "ftth-redis-service")
cache = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

@app.route('/status')
def status():
    try:
        cache.ping()
        return jsonify({
            "status": "OK",
            "message": "Backend conectado a Redis exitosamente",
            "ftth_network": "Online"
        })
    except redis.ConnectionError:
        return jsonify({
            "status": "ERROR",
            "message": "No se pudo conectar a Redis",
            "ftth_network": "Offline"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Patrones obligatorios al agregar código

**Variables de entorno** — siempre con valor por defecto:
```python
variable = os.getenv("NOMBRE_ENV", "valor-por-defecto")
```

**Respuestas JSON** — siempre `jsonify({})`, nunca strings directos:
```python
return jsonify({"campo": "valor", "campo2": "valor2"})
```

**Error handling** — mismo patrón try/except que el existente:
```python
try:
    # operación que puede fallar
except redis.ConnectionError:
    return jsonify({"status": "ERROR", "mensaje": "..."}), 500
```

**Nuevo endpoint** — mismo estilo que `/status`:
```python
@app.route('/nuevo-endpoint')
def nuevo_endpoint():
    try:
        # lógica
        return jsonify({"status": "OK", "campo": "valor"})
    except Exception as e:
        return jsonify({"status": "ERROR", "mensaje": str(e)}), 500
```

---

## Dependencias Python

### Estado actual de `requirements.txt`

```
Flask==3.0.0
redis==5.0.1
```

### Reglas para agregar dependencias

1. **Siempre versión fija** (`paquete==X.Y.Z`), nunca rangos (`>=`, `~=`)
2. Antes de agregar, verificar que la dependencia no sea transitiva (ya incluida por Flask o redis)
3. Considerar el impacto en el tamaño de la imagen Alpine (preferir librerías pequeñas)
4. Documentar por qué se necesita en un comentario inline si no es obvio

---

## Backend — Dockerfile

```dockerfile
FROM python:3.9-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Reglas para modificar el Dockerfile

- Mantener la imagen base `python:3.9-alpine` (pesa ~50MB vs ~900MB de Debian)
- Preservar el orden: `COPY requirements.txt` → `RUN pip install` → `COPY app.py`
  (optimización de caché de capas Docker)
- Si se agrega un nuevo archivo fuente → `COPY nuevo_archivo.py .` DESPUÉS del `pip install`
- Nunca usar `COPY . .` (copia archivos innecesarios y rompe el caché de pip)

---

## Frontend — Información Clave

### Nginx sirve el HTML del ConfigMap, no del filesystem local

El contenedor Nginx monta el ConfigMap `ftth-dashboard-html` en `/usr/share/nginx/html/`. Para cambiar el contenido del dashboard:
1. Editar `k8s/02-storage/frontend-configmap.yaml`
2. `kubectl apply -f k8s/02-storage/frontend-configmap.yaml`
3. El kubelet propaga el cambio en ~1 minuto, o forzar: `kubectl rollout restart deployment/ftth-frontend`

### Frontend — Dockerfile

```dockerfile
FROM nginx:alpine
# Sin COPY de archivos — el contenido viene del ConfigMap montado como volumen
EXPOSE 80
```

El Dockerfile es mínimo por diseño. No hay nada que copiar porque el HTML vive en el ConfigMap.

---

## Contrato de la API — `/status`

El único endpoint actual. Su contrato es:

| Campo | Tipo | Valores posibles |
|---|---|---|
| `status` | string | `"OK"` o `"ERROR"` |
| `message` | string | Descripción del estado |
| `ftth_network` | string | `"Online"` o `"Offline"` |

HTTP Status codes: `200` cuando Redis responde, `500` cuando no.

**Regla**: cualquier nuevo endpoint debe incluir al menos `"status"` en su respuesta para mantener coherencia de la API.

---

## Variables de Entorno del Backend

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `REDIS_HOST` | `ftth-redis-service` | DNS interno del Service de Redis en K8s |

Si se agrega una nueva variable de entorno, coordinar con Infrastructure Agent para agregar la entrada `env:` correspondiente en `k8s/03-deployments/backend-deployment.yaml`.


## Content from agent_protocol.md

# Application Agent — Protocolo de Operación

> **ROL**: Especialista en código fuente. Dominio: `src/backend/` y `src/frontend/`.
> **ACTIVACIÓN**: Paralela — corre junto con otros agentes de dominio en la fase de trabajo.
> **CONOCIMIENTO**: Leer `app_skill.md` antes de operar.

---

## Condiciones de Activación

El Orquestador me invoca cuando:

| Trigger | Acción esperada |
|---|---|
| "Agregar un nuevo endpoint al backend" | Proponer código Flask + test unitario |
| "Cambiar la lógica del health check" | Modificar `app.py` respetando el estilo existente |
| "Agregar una nueva dependencia Python" | Actualizar `requirements.txt` con versión fija |
| "Optimizar el Dockerfile" | Proponer mejoras de capas y tamaño de imagen |
| "Detectar vulnerabilidades en dependencias" | Analizar `requirements.txt` con `pip-audit` |
| "Cambiar el contenido del dashboard" | Proponer cambios al HTML del Frontend |
| "Validar que no hay credenciales hardcodeadas" | Escanear `src/` buscando patrones de secretos |

**NO me actives si**:
- El cambio es de manifiestos K8s (→ Infrastructure Agent)
- El cambio es de pipeline CI/CD (→ CI/CD Agent)
- La consulta es sobre el estado runtime del Pod (→ Validation Agent)

---

## Contrato de Input

```
APPLICATION REQUEST
───────────────────
Tipo:        [nuevo endpoint | modificación | análisis | refactor]
Componente:  [backend | frontend]
Descripción: [qué se necesita en 2-3 oraciones]
Contexto:    [endpoint o función específica afectada]
```

---

## Mi Proceso — 6 Pasos

### Paso 0 — Cargar memoria del proyecto (HarnessDB)
```bash
# Consultar decisiones relevantes al dominio de la aplicación
python3 .harness/scripts/harness-query.py --decisions --domain architecture

# Verificar lecciones aprendidas del agente de aplicación
python3 .harness/scripts/harness-query.py --lessons --agent application

# Buscar contexto específico si el pedido menciona un componente
python3 .harness/scripts/harness-query.py --search "[término-clave]"
```
Usar esta información para evitar repetir errores y mantener coherencia con decisiones previas.

### Paso 1 — Cargar contexto de archivos
```
1a. Leer app_skill.md (patrones de código de este proyecto)
1b. Leer los archivos afectados: app.py, requirements.txt, Dockerfile
1c. Entender la estructura existente antes de proponer cambios
```

### Paso 2 — Analizar impacto
- ¿El cambio modifica el contrato de la API? (endpoint, método HTTP, respuesta JSON)
- ¿Requiere nueva dependencia en `requirements.txt`?
- ¿Requiere nueva variable de entorno? (→ coordinar con Infrastructure Agent para el Deployment)
- ¿Cambia el puerto o el host de Flask?

### Paso 3 — Proponer cambios
- Entregar el diff de código real (no pseudocódigo)
- Proponer siempre el caso de test correspondiente
- Si agrega dependencia → especificar versión exacta (`Flask==3.0.0`, no `Flask>=3.0`)
- Si cambia el contrato de la API → notificar al Orquestador para coordinar con Infrastructure Agent

### Paso 4 — Checklist pre-entrega
- [ ] El código sigue el estilo de `app.py` (no mezcla paradigmas)
- [ ] Las variables de entorno se leen con `os.getenv("VAR", "default")`
- [ ] Los endpoints retornan `jsonify({})` con las mismas claves que los existentes
- [ ] El error handling usa el mismo patrón `try/except redis.ConnectionError`
- [ ] Si hay nueva dependencia → está en `requirements.txt` con versión fija
- [ ] No hay credenciales, IPs ni puertos hardcodeados en el código

### Paso 5 — Registrar en HarnessDB (obligatorio)

Al finalizar, registrar en la memoria del proyecto:

```bash
# Si se tomó una decisión de diseño significativa:
python3 .harness/scripts/harness-write.py decision \
  --agent application \
  --domain architecture \
  --title "[título]" \
  --context "[por qué]" \
  --decision "[qué se decidió]"

# Si se descubrió algo relevante:
python3 .harness/scripts/harness-write.py lesson \
  --agent application \
  --category [error|pattern|tip] \
  --title "[título]" \
  --description "[descripción]"

# Siempre registrar la actividad:
python3 .harness/scripts/harness-write.py activity \
  --agent application \
  --action [create|modify] \
  --target "[archivo afectado]" \
  --summary "[resumen]"
```

---

## Contrato de Output

```
APPLICATION PROPOSAL
────────────────────
Archivos a modificar: [lista con rutas]
Diff propuesto:       [cambios en formato diff]
Nuevas dependencias:  [si aplica, con versiones exactas]
Variables de entorno: [nuevas envs requeridas — coordinar con Infrastructure Agent]
Test sugerido:        [caso de prueba para el cambio]
Breaking changes:     [si el contrato de la API cambió]
```

---

## Reglas de Escalamiento

Escalo al Orquestador si:
- El cambio requiere nueva variable de entorno → Infrastructure Agent debe actualizar el Deployment
- El cambio modifica el puerto 5000 o el host `0.0.0.0` → Infrastructure Agent debe actualizar los Services
- Se necesita una nueva imagen Docker → CI/CD Agent debe actualizar el pipeline