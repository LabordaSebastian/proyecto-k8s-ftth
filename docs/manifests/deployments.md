# Deployments

Esta sección documenta todos los recursos de tipo `Deployment` y `CronJob` ubicados en `k8s/03-deployments/`. Son los Workloads principales del clúster: los procesos que corren indefinidamente (o periódicamente) para dar vida a la plataforma FTTH.

## Resumen de Workloads

| Archivo | Nombre | Réplicas | Imagen | Tipo |
|---|---|---|---|---|
| `frontend-deployment.yaml` | `ftth-frontend` | 2 | `nginx:alpine` | Deployment |
| `backend-deployment.yaml` | `ftth-backend` | 2 | `ftth-backend:v1` (local) | Deployment |
| `redis-deployment.yaml` | `ftth-redis` | 1 | `redis:alpine` | Deployment |
| `network-checker-cronjob.yaml` | `ftth-network-checker` | N/A | `busybox:latest` | CronJob |

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
```

**Decisiones clave:**

- **`imagePullPolicy: Never`** — Imagen construida y cargada localmente en Kind. Sin esta directiva, Kubernetes intentaría descargarla de internet y fallaría con `ErrImageNeverPull`.
- **Variable de entorno `REDIS_HOST`** — Inyecta la dirección del Service de Redis. La API Python la consume via `os.getenv()`, desacoplando el código de la infraestructura.
- **`replicas: 2`** — La API es stateless, puede escalar horizontalmente sin coordinación entre réplicas.

!!! warning "Prerrequisito antes de aplicar este Deployment"
    La imagen `ftth-backend:v1` debe estar construida e inyectada en Kind **antes** de aplicar este manifiesto:
    ```bash
    docker build -t ftth-backend:v1 ./src/backend/
    kind load docker-image ftth-backend:v1 --name ftth-cluster
    ```

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

### Rolling Update sin downtime

Para actualizar la imagen del Backend a una nueva versión:

```bash
# 1. Construir la nueva versión
docker build -t ftth-backend:v2 ./src/backend/

# 2. Inyectarla en Kind
kind load docker-image ftth-backend:v2 --name ftth-cluster

# 3. Actualizar el Deployment (estrategia RollingUpdate por defecto)
kubectl set image deployment/ftth-backend python-api=ftth-backend:v2

# 4. Monitorear el progreso del rollout
kubectl rollout status deployment/ftth-backend
```

### Revertir a la versión anterior

```bash
kubectl rollout undo deployment/ftth-backend
```

### Escalar un Deployment manualmente

```bash
# Escalar el Backend a 3 réplicas
kubectl scale deployment ftth-backend --replicas=3

# Volver a 2
kubectl scale deployment ftth-backend --replicas=2
```
