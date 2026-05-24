# Deployments

Esta sección documenta todos los recursos de tipo `Deployment` y `CronJob` ubicados en `k8s/03-deployments/`. Son los Workloads principales del clúster: los procesos que corren indefinidamente (o periódicamente) para dar vida a la plataforma FTTH.

## Resumen de Workloads

| Archivo | Nombre | Réplicas | Imagen | Tipo |
|---|---|---|---|---|---|
| `frontend-deployment.yaml` | `ftth-frontend` | 2 | `nginx:alpine` | Deployment |
| `backend-deployment.yaml` | `ftth-backend` | 2 | `ftth-backend:v1` (local) | Deployment |
| `redis-deployment.yaml` | `ftth-redis` | 1 | `redis:alpine` | Deployment |
| `network-checker-cronjob.yaml` | `ftth-network-checker` | N/A | `busybox:latest` | CronJob |
| `pod-disruption-budgets.yaml` | `ftth-backend-pdb`, `ftth-frontend-pdb` | N/A | N/A | PodDisruptionBudget |

!!! tip "Para la documentación detallada de cada componente"
    Esta sección es una referencia rápida de los manifiestos. Para el desglose arquitectónico completo (por qué se tomó cada decisión de diseño), consulta la sección [Arquitectura](../architecture/index.md).

---

## Frontend Deployment

**Archivo:** `k8s/03-deployments/frontend-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ftth-frontend
  labels:
    app: ftth-frontend
    tier: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ftth-frontend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: ftth-frontend
    spec:
      containers:
      - name: nginx-web
        image: nginx:alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 2
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 15
          periodSeconds: 20
          timeoutSeconds: 2
          failureThreshold: 3
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 30"]
        volumeMounts:
        - name: html-volume
          mountPath: /usr/share/nginx/html
      volumes:
      - name: html-volume
        configMap:
          name: ftth-dashboard-html
```

**Decisiones clave:**

- **`replicas: 2`** — Alta disponibilidad. Si un Pod falla, el otro continúa sirviendo tráfico mientras el Deployment crea el reemplazo.
- **`image: nginx:alpine`** — Imagen pública. Usa `IfNotPresent` por defecto (no declarado explícitamente).
- **Volumen desde ConfigMap** — El HTML del dashboard se inyecta en `/usr/share/nginx/html` sin necesidad de reconstruir la imagen. Ver [Frontend (Nginx)](../architecture/frontend.md) para más detalles.

#### `maxSurge: 1` y `maxUnavailable: 0` — Rolling Update sin downtime

Esta estrategia garantiza que **siempre haya al menos 2 pods sirviendo tráfico** durante una actualización. `maxUnavailable: 0` impide que K8s mate pods viejos antes de que los nuevos estén listos. Combinado con `maxSurge: 1`, el Deployment crea 1 pod extra, espera a que pase la readiness probe, y recién entonces termina el pod viejo.

#### `readinessProbe` — El semáforo de tráfico

Kubernetes no envía tráfico del Service a un Pod hasta que la readiness probe responde HTTP 200. Durante un Rolling Update, el nuevo Pod solo recibe tráfico cuando Nginx está listo para servir. Si la probe falla, el pod se marca como `NotReady` y el Service lo excluye automáticamente.

#### `lifecycle.preStop` — La llave para conexiones gracefully

```yaml
command: ["/bin/sh", "-c", "sleep 30"]
```

Cuando K8s decide terminar un Pod, el orden es: (1) ejecuta `preStop`, (2) envía `SIGTERM`, (3) espera `terminationGracePeriodSeconds` (default 30s), (4) envía `SIGKILL`. Este `sleep 30` dentro del preStop retrasa la `SIGTERM` 30 segundos adicionales, dando tiempo a que el balanceador de carga (kube-proxy) actualice sus reglas y deje de enrutar tráfico al Pod que se va a morir. Sin esto, algunas conexiones en curso recibirían un RST (reset) y el usuario vería un error.

!!! warning "`sleep 30` es un patrón de laboratorio"
    En producción se usa un hook `preStop` que envía una señal real de graceful shutdown a Nginx (`nginx -s quit`). El `sleep` es un atajo válido para este entorno local.

---

## Backend Deployment

**Archivo:** `k8s/03-deployments/backend-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ftth-backend
  labels:
    app: ftth-backend
    tier: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ftth-backend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: ftth-backend
    spec:
      containers:
      - name: python-api
        image: ftth-backend:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 5000
        env:
        - name: REDIS_HOST
          value: "ftth-redis-service"
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 2
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 15
          periodSeconds: 20
          timeoutSeconds: 2
          failureThreshold: 3
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 30"]
```

**Decisiones clave:**

- **`imagePullPolicy: Never`** — Imagen construida y cargada localmente en Kind. Sin esta directiva, Kubernetes intentaría descargarla de internet y fallaría con `ErrImageNeverPull`.
- **Variable de entorno `REDIS_HOST`** — Inyecta la dirección del Service de Redis. La API Python la consume via `os.getenv()`, desacoplando el código de la infraestructura.
- **`replicas: 2`** — La API es stateless, puede escalar horizontalmente sin coordinación entre réplicas.

#### `readinessProbe` vs `livenessProbe` — Dos tipos de health check

| Probe | Endpoint | Propósito |
|---|---|---|
| `readinessProbe` | `GET /health` | Solo decide si el Pod recibe tráfico |
| `livenessProbe` | `GET /health` | Decide si K8s debe reiniciar el Pod |

Ambas apuntan al mismo endpoint `/health` implementado en `app.py`, que verifica que la app responde HTTP 200 **y** que Redis es accesible (retorna 503 si Redis está caído). La diferencia está en la acción: la `readiness` aísla el Pod del Service, la `liveness` fuerza un reinicio.

!!! tip "`failureThreshold` — Tolerancia a fallos transitorios"
    `failureThreshold: 3` significa que Kubernetes necesita 3 fallos consecutivos (30 segundos) antes de considerar el Pod como no saludable. Esto evita falsos positivos por latencias de red momentáneas.

#### `lifecycle.preStop` — Graceful shutdown

```yaml
command: ["/bin/sh", "-c", "sleep 30"]
```

El `sleep 30` dentro del hook `preStop` retrasa el envío de `SIGTERM` al proceso Flask, dando tiempo a que el Service de Kubernetes actualice sus endpoints (iptables/ipvs) y deje de enviar tráfico al Pod saliente. Sin este hook, las peticiones en curso recibirían un `Connection refused` o timeout.

!!! warning "Prerrequisito antes de aplicar este Deployment"
    La imagen `ftth-backend:v1` debe estar construida e inyectada en Kind **antes** de aplicar este manifiesto:
    ```bash
    docker build -t ftth-backend:v1 ./src/backend/
    kind load docker-image ftth-backend:v1 --name ftth-cluster
    ```

---

## PodDisruptionBudgets

**Archivo:** `k8s/03-deployments/pod-disruption-budgets.yaml`

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ftth-backend-pdb
  namespace: default
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: ftth-backend
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ftth-frontend-pdb
  namespace: default
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: ftth-frontend
```

**Decisiones clave:**

- **`minAvailable: 1`** — Garantiza que al menos 1 Pod de cada Deployment esté siempre disponible, incluso durante operaciones de drenado de nodos o disruptiones voluntarias.
- **Afecta solo disruptiones voluntarias** — No protege contra fallos de nodo, OOMKilled, o crashes del Pod. Solo aplica cuando el cluster decide terminar pods proactivamente (ej: `kubectl drain`, `kubectl delete pod`, actualizaciones de nodo).

#### ¿Por qué `minAvailable: 1` y no `maxUnavailable`?

Ambos son equivalentes cuando hay 2 réplicas (`minAvailable: 1` = `maxUnavailable: 1`). Se eligió `minAvailable` porque expresa mejor la intención: "siempre quiero al menos un Pod sirviendo", en lugar de "puedo tolerar perder uno". Es semánticamente más claro para un laboratorio de estudio CKA.

!!! info "PDB + RollingUpdate = protección en capas"
    El RollingUpdate con `maxUnavailable: 0` protege durante las actualizaciones. El PDB con `minAvailable: 1` protege durante operaciones administrativas (drenado de nodo, borrado manual). Juntos cubren todos los escenarios de interrupción controlada.

---

## Redis Deployment

**Archivo:** `k8s/03-deployments/redis-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ftth-redis
  labels:
    app: ftth-redis
    tier: database
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ftth-redis
  template:
    metadata:
      labels:
        app: ftth-redis
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: role
                operator: In
                values:
                - database
      containers:
      - name: redis-cache
        image: redis:alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
```

**Decisiones clave:**

- **`replicas: 1`** — Redis es stateful. Múltiples réplicas sin replicación configura requerirían Redis Sentinel o Redis Cluster.
- **`nodeAffinity: required`** — Variante **hard** del Node Affinity. El Pod nunca se programa en un nodo que no tenga el label `role=database`. Si no hay nodos disponibles, el Pod queda en `Pending`. El nodo Worker tiene ese label declarado en `kind-config.yaml`.

!!! info "¿Por qué un Deployment y no un StatefulSet?"
    En producción, Redis se gestionaría con un `StatefulSet` para garantizar identidad de red estable y almacenamiento persistente por réplica. En este laboratorio se usa `Deployment` por simplicidad, aceptando que los datos en memoria se pierden si el Pod se reinicia.

---

## Network Checker CronJob

**Archivo:** `k8s/03-deployments/network-checker-cronjob.yaml`

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ftth-network-checker
  labels:
    app: ftth-network-checker
    tier: worker
spec:
  schedule: "*/2 * * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: checker
            image: busybox:latest
            imagePullPolicy: IfNotPresent
            command:
            - /bin/sh
            - -c
            - |
              echo "--- Iniciando chequeo de salud de la red FTTH ---"
              date
              wget -qO- http://ftth-backend-service:5000/status || echo "¡Alerta! Fallo al conectar con el Backend de la red."
              echo -e "\n--- Chequeo finalizado exitosamente ---"
            resources:
              requests:
                memory: "16Mi"
                cpu: "10m"
              limits:
                memory: "32Mi"
                cpu: "50m"
          restartPolicy: OnFailure
```

**Decisiones clave:**

- **`schedule: "*/2 * * * *"`** — Ejecuta el chequeo cada 2 minutos usando sintaxis estándar CRON.
- **`restartPolicy: OnFailure`** — Obligatorio para Jobs. `Always` (el default de Deployments) está prohibido en Jobs y CronJobs porque reinicaría el Pod incluso cuando completa con éxito.
- **`image: busybox:latest`** — Imagen de ~2 MB con `wget`, `sh` y utilidades de diagnóstico. Ideal para tareas efímeras de scripting.
- **`successfulJobsHistoryLimit: 3` / `failedJobsHistoryLimit: 1`** — Controla la acumulación de Jobs y Pods completados en `etcd` para evitar degradación de rendimiento.

---

## Comparativa de Resource Requests/Limits

Todos los Workloads siguen el mismo patrón de resource governance para proteger el clúster de consumo descontrolado:

| Workload | CPU Request | CPU Limit | RAM Request | RAM Limit | Justificación |
|---|---|---|---|---|---|
| Frontend (Nginx) | `50m` | `100m` | `64Mi` | `128Mi` | Servidor web estático, baja carga de CPU |
| Backend (Flask) | `50m` | `100m` | `64Mi` | `128Mi` | API ligera, lógica simple |
| Redis | `50m` | `100m` | `64Mi` | `128Mi` | Dataset pequeño en memoria |
| Network Checker | `10m` | `50m` | `16Mi` | `32Mi` | Script de ~2 segundos, mínimo overhead |

!!! info "Unidades de medida en Kubernetes"
    - **CPU**: Se mide en **milicores** (`m`). `1000m = 1 núcleo de CPU`. `50m` equivale al 5% de un núcleo.
    - **Memoria**: Se mide en **Mebibytes** (`Mi`) o Megabytes (`M`). `1 Mi = 1.048.576 bytes`. En la práctica, `Mi` y `MB` son intercambiables en estimaciones.

---

## Instrucciones de Operación

### Aplicar todos los Deployments

El orden de aplicación importa: el ConfigMap del Frontend debe existir antes de que el Pod de Nginx arranque.

```bash
# Paso 1: ConfigMap (dependencia del Frontend)
kubectl apply -f k8s/02-storage/frontend-configmap.yaml

# Paso 2: Todos los Deployments y CronJob
kubectl apply -f k8s/03-deployments/
```

### Verificar el estado de todos los Workloads

```bash
# Vista general de todos los Deployments
kubectl get deployments

# Vista general del CronJob
kubectl get cronjobs

# Ver todos los Pods del namespace con su nodo asignado
kubectl get pods -o wide
```

El output esperado cuando el clúster está sano:

```
NAME             READY   UP-TO-DATE   AVAILABLE   AGE
ftth-backend     2/2     2            2           5m
ftth-frontend    2/2     2            2           5m
ftth-redis       1/1     1            1           5m
```

### Verificar el consumo real de recursos (requiere Metrics Server)

```bash
# Ver consumo de CPU y RAM por Pod
kubectl top pods

# Ver consumo por nodo
kubectl top nodes
```

### Rolling Update — Zero-downtime

La estrategia `maxUnavailable: 0` + `maxSurge: 1` combinada con probes y preStop garantiza **cero downtime** durante las actualizaciones.

Para actualizar el Backend a una nueva versión:

```bash
# 1. Construir la nueva versión
BACKEND_VERSION=v2 ./manage-env.sh up

# O manualmente:
docker build -t ftth-backend:v2 ./src/backend/
kind load docker-image ftth-backend:v2 --name ftth-cluster

# 2. Hacer el Rolling Update (nombre del container: python-api)
kubectl set image deployment/ftth-backend python-api=ftth-backend:v2

# 3. Registrar el cambio en el historial (reemplaza a --record, deprecated)
kubectl annotate deployment/ftth-backend \
  kubernetes.io/change-cause="Actualización a v2" \
  --overwrite

# 4. Monitorear el progreso
kubectl rollout status deployment/ftth-backend --timeout=5m

# 5. Verificar el historial de revisiones
kubectl rollout history deployment/ftth-backend
```

!!! warning "`--record` está deprecated en K8s 1.29+"
    Usar `kubectl annotate kubernetes.io/change-cause` en su lugar. Sin este paso, el rollout history mostrará `<none>` como change-cause.

Para simular un Rolling Update sin cambiar de imagen (útil para probar el mecanismo):

```bash
# Forzar un cambio en el template del Pod
kubectl set env deployment/ftth-backend DEPLOY_TIMESTAMP=$(date +%s)
kubectl annotate deployment/ftth-backend \
  kubernetes.io/change-cause="Trigger zero-downtime test" \
  --overwrite
```

#### Monitorear en vivo

```bash
# Terminal 1: Ver progreso de pods
kubectl get pods -w -l app=ftth-backend

# Terminal 2: Verificar que NO hay downtime
while true; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:30080 2>/dev/null)
  if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ $(date +%H:%M:%S) - HTTP $HTTP_CODE"
  else
    echo "❌ $(date +%H:%M:%S) - HTTP $HTTP_CODE - DOWNTIME!"
  fi
  sleep 0.5
done
```

Output esperado durante un Rolling Update exitoso:

```
✅ 20:46:43 - HTTP 200
✅ 20:46:44 - HTTP 200
✅ 20:46:44 - HTTP 200
... (nunca aparece ❌)
```

### Revertir a la versión anterior

```bash
# Opción 1: Script automático (recomendado)
./scripts/rollback.sh

# Opción 2: Manual
kubectl rollout undo deployment/ftth-backend
kubectl annotate deployment/ftth-backend \
  kubernetes.io/change-cause="Rollback manual" \
  --overwrite
kubectl rollout status deployment/ftth-backend --timeout=5m
```

El script `scripts/rollback.sh` automatiza el proceso completo: revierte ambos deployments (Backend y Frontend), espera a que los rollouts terminen, valida que los endpoints respondan, y muestra el historial antes y después.

!!! tip "Requisito: al menos 2 revisiones en el historial"
    Para hacer rollback debe haber al menos 2 revisiones en `kubectl rollout history`. Si solo hay 1 (el deployment nunca se modificó), el script lo detecta y muestra un mensaje claro. En ese caso, primero hacé un cambio como se describe arriba.

### Escalar un Deployment manualmente

```bash
# Escalar el Backend a 3 réplicas
kubectl scale deployment ftth-backend --replicas=3

# Volver a 2
kubectl scale deployment ftth-backend --replicas=2
```
