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
