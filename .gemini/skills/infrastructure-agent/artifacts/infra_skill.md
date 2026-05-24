# Infrastructure Agent — Knowledge Base (infra_skill.md)

> Conocimiento específico del proyecto para el Infrastructure Agent.
> Leer junto con `agent_protocol.md` antes de operar.

---

## Mapa de Recursos del Clúster

### Topología actual

```
Clúster: ftth-cluster (Kind)
├── control-plane: ftth-cluster-control-plane
│   ├── Puerto 30080 → ftth-frontend-service (NodePort)
│   └── Puerto 30088 → KubeView (NodePort)
└── worker: ftth-cluster-worker
    └── labels: role=database, disktype=ssd
        └── Redis se programa aquí (nodeAffinity / nodeSelector)
```

### Inventario de recursos actuales

| Tipo | Nombre | Namespace | Archivo |
|---|---|---|---|
| `Deployment` | `ftth-frontend` | `default` | `k8s/03-deployments/frontend-deployment.yaml` |
| `Deployment` | `ftth-backend` | `default` | `k8s/03-deployments/backend-deployment.yaml` |
| `Deployment` | `ftth-redis` | `default` | `k8s/03-deployments/redis-deployment.yaml` |
| `CronJob` | `ftth-network-checker` | `default` | `k8s/03-deployments/network-checker-cronjob.yaml` |
| `Service` | `ftth-frontend-service` | `default` | `k8s/05-services/frontend-service.yaml` |
| `Service` | `ftth-backend-service` | `default` | `k8s/05-services/backend-service.yaml` |
| `Service` | `ftth-redis-service` | `default` | `k8s/05-services/redis-service.yaml` |
| `ConfigMap` | `ftth-dashboard-html` | `default` | `k8s/02-storage/frontend-configmap.yaml` |

### Dependencias entre servicios

```
Browser (host)
  └─[NodePort:30080]─→ ftth-frontend-service
                          └─[ClusterIP:80]─→ ftth-frontend (Nginx)
                                               └─[Volume]─→ ConfigMap ftth-dashboard-html

CronJob ftth-network-checker (cada 2 min)
  └─[ClusterIP:5000]─→ ftth-backend-service
                          └─[ClusterIP:5000]─→ ftth-backend (Flask)
                                                └─[ClusterIP:6379]─→ ftth-redis-service
                                                                        └─ ftth-redis (Redis)
```

---

## Convenciones de Manifiestos

### Nomenclatura

| Elemento | Patrón | Ejemplos actuales |
|---|---|---|
| Nombre del recurso | `ftth-[componente]` | `ftth-backend`, `ftth-redis` |
| Nombre del Service | `ftth-[componente]-service` | `ftth-backend-service` |
| Label `app:` | `ftth-[componente]` | `app: ftth-backend` |
| Label `tier:` | `frontend` / `backend` / `data` / `worker` | `tier: backend` |
| Imagen Docker local | `ftth-[componente]:v[N]` | `ftth-backend:v1` |
| Imagen pública | `[imagen]:[tag-fijo]` | `nginx:alpine`, `redis:alpine`, `busybox:latest` |

### Rutas de archivos

```
k8s/
├── 01-namespaces-rbac/   ← Namespaces, RBAC, ServiceAccounts
├── 02-storage/           ← ConfigMaps, PersistentVolumes, Secrets
├── 03-deployments/       ← Deployments, StatefulSets, CronJobs, DaemonSets
├── 04-security/          ← NetworkPolicy, PodSecurityPolicy, EncryptionConfig
├── 05-services/          ← Services (ClusterIP, NodePort, LoadBalancer)
└── 06-metrics/           ← Metrics Server, HPA, VPA
```

### Template de Deployment (patrón del proyecto)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ftth-[componente]
  labels:
    app: ftth-[componente]
    tier: [frontend|backend|data|worker]
spec:
  replicas: [N]
  selector:
    matchLabels:
      app: ftth-[componente]
  template:
    metadata:
      labels:
        app: ftth-[componente]
    spec:
      containers:
      - name: [nombre-contenedor]
        image: [imagen]:[tag]
        imagePullPolicy: [Never|IfNotPresent|Always]
        ports:
        - containerPort: [puerto]
        resources:
          requests:
            memory: "[N]Mi"
            cpu: "[N]m"
          limits:
            memory: "[N]Mi"
            cpu: "[N]m"
```

### Template de Service (patrón del proyecto)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ftth-[componente]-service
spec:
  type: [ClusterIP|NodePort]
  selector:
    app: ftth-[componente]      # DEBE coincidir con el label del Deployment
  ports:
    - port: [puerto]
      targetPort: [puerto]
      # Solo para NodePort:
      # nodePort: 3XXXX
```

---

## Reglas de Configuración

### `imagePullPolicy`

| Tipo de imagen | Política correcta | Razón |
|---|---|---|
| Imagen local (`ftth-backend:v1`) | `Never` | No existe en ningún registry; se carga con `kind load` |
| Imagen pública oficial (`nginx:alpine`) | `IfNotPresent` | Evita pulls redundantes en cada reinicio de Pod |
| Imagen en desarrollo activo | `Always` | Para garantizar la versión más reciente en cada deploy |

### Resource Requests y Limits — Valores de referencia

| Componente | Memory Request | Memory Limit | CPU Request | CPU Limit |
|---|---|---|---|---|
| Nginx (Frontend) | `64Mi` | `128Mi` | `50m` | `100m` |
| Flask (Backend) | `64Mi` | `128Mi` | `50m` | `100m` |
| Redis | `64Mi` | `128Mi` | `50m` | `100m` |
| BusyBox (CronJob) | `16Mi` | `32Mi` | `10m` | `50m` |
| Nuevo componente ligero | `64Mi` | `128Mi` | `50m` | `100m` |
| Nuevo componente pesado | `128Mi` | `256Mi` | `100m` | `200m` |

### Tipos de Service — Cuándo usar cada uno

| Tipo | Cuándo usarlo en este proyecto |
|---|---|
| `ClusterIP` | Servicios internos: Backend, Redis. Nunca expuestos al host. |
| `NodePort` | Servicios accesibles desde el host: Frontend (30080), KubeView (30088). |
| `LoadBalancer` | No se usa en Kind (requiere cloud provider o MetalLB). |

### Puertos NodePort reservados en `kind-config.yaml`

| Puerto | Servicio |
|---|---|
| `30080` | Frontend FTTH Dashboard |
| `30088` | KubeView (visualización del clúster) |

Si se necesita exponer un nuevo servicio, se debe agregar un nuevo `extraPortMappings` en `kind-config.yaml` **y recrear el clúster**.

---

## Directorio `k8s/04-security/` — Estado Actual

El directorio existe pero está vacío. Es el candidato natural para:
- `NetworkPolicy` — restringir tráfico entre pods (ej: solo el CronJob puede llamar al Backend)
- `EncryptionConfiguration` — referencia al archivo `enc.yaml` en el control plane
- `PodSecurityPolicy` / `PodSecurityAdmission` — restricciones de privilegios en contenedores

Al agregar cualquier recurso aquí, actualizar también `docs/security/`.
