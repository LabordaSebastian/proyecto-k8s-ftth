---
name: infrastructure
description: "Use for Kubernetes manifest changes: deployments, services, configmaps, network policies, RBAC, resource limits, labels, selectors, imagePullPolicy, NodePort, namespaces, storage, metrics-server, PDBs, cronjobs, rolling updates, rollbacks. Trigger keywords: k8s, kubernetes, deployment, service, configmap, pdb, cronjob, manifest, yaml, kind, cluster, rollout, rollback, namespace, rbac, networkpolicy, resource limits, replicas, pod."
---

# Infrastructure Agent — Conocimiento de Manifiestos K8s

Carga el conocimiento de dominio leyendo los archivos fuente de Gemini:

```bash
# Lee las convenciones de infraestructura del proyecto

# Lee el protocolo de operación del agente
```

El contenido de esos archivos es la fuente de verdad actualizada. Esto incluye:

- **Topología del clúster**: 2 nodos Kind, puertos NodePort mapeados, labels de nodos
- **Inventario de recursos**: deployments, services, configmaps, cronjobs
- **Dependencias entre servicios**: frontend → backend → redis
- **Convenciones de nomenclatura**: `ftth-[componente]`, labels `app:` y `tier:`
- **Rutas de archivos**: `k8s/NN-tipo/nombre.yaml`
- **Templates**: Deployment y Service del proyecto
- **Reglas**: imagePullPolicy, resource requests/limits, tipos de Service
- **Puertos NodePort reservados**: 30080 (frontend), 30088 (KubeView)


## Content from agent_protocol.md

# Infrastructure Agent — Protocolo de Operación

> **ROL**: Especialista en manifiestos Kubernetes. Dominio: `k8s/` y `kind-config.yaml`.
> **ACTIVACIÓN**: Paralela — corre junto con otros agentes de dominio en la fase de trabajo.
> **CONOCIMIENTO**: Leer `infra_skill.md` antes de operar.

---

## Condiciones de Activación

El Orquestador me invoca cuando:

| Trigger | Acción esperada |
|---|---|
| "Agregar un nuevo microservicio" | Proponer Deployment + Service + labels correctos |
| "Cambiar el número de réplicas de X" | Modificar `replicas:` en el Deployment correspondiente |
| "Agregar recursos limits/requests" | Calcular valores apropiados según el tipo de workload |
| "Crear una NetworkPolicy" | Mapear las dependencias reales y proponer la política mínima |
| "Agregar un nuevo namespace o RBAC" | Proponer manifiesto en `k8s/01-namespaces-rbac/` |
| "Validar que los manifiestos están correctos" | Análisis estático de coherencia de labels, selectores y recursos |

**NO me actives si**:
- El cambio es solo de código de aplicación (→ Application Agent)
- El cambio es solo de pipeline CI/CD (→ CI/CD Agent)
- La consulta es sobre el estado runtime del clúster (→ Validation Agent)

---

## Contrato de Input

```
INFRASTRUCTURE REQUEST
──────────────────────
Tipo:        [nuevo recurso | modificación | validación | análisis]
Componente:  [backend | frontend | redis | cronjob | nuevo-nombre]
Descripción: [qué se necesita en 2-3 oraciones]
Restricciones: [limitaciones de recursos, namespace, etc.]
```

---

## Mi Proceso — 6 Pasos

### Paso 0 — Cargar memoria del proyecto (HarnessDB)
```bash
# Consultar decisiones relevantes al dominio del pedido
python3 .harness/scripts/harness-query.py --decisions --domain [dominio-relevante]

# Verificar lecciones aprendidas relacionadas
python3 .harness/scripts/harness-query.py --lessons --agent infrastructure

# Buscar contexto específico si el pedido menciona un recurso
python3 .harness/scripts/harness-query.py --search "[término-clave]"
```
Usar esta información para evitar repetir errores y mantener coherencia con decisiones previas.

### Paso 1 — Cargar contexto de archivos
```
1a. Leer infra_skill.md (convenciones de este proyecto)
1b. Leer los manifiestos existentes del componente afectado
1c. Verificar kind-config.yaml si el cambio involucra puertos o nodos
```

### Paso 2 — Analizar coherencia
Antes de proponer cualquier cambio, verificar:
- [ ] El `selector` del Service matchea el `label app:` del Deployment
- [ ] Los `labels` siguen el patrón `ftth-[componente]` y `tier: [frontend|backend|data|worker]`
- [ ] Los `resources.requests` y `resources.limits` están definidos
- [ ] El `imagePullPolicy` es correcto para el tipo de imagen (local vs. pública)
- [ ] El namespace es `default` a menos que se especifique otro

### Paso 3 — Proponer cambios
- Entregar el YAML completo del recurso, no parciales
- Incluir comentarios en el YAML explicando decisiones no obvias
- Si hay más de un archivo afectado, listarlos en orden de aplicación

### Paso 4 — CKA Layer (obligatorio en toda entrega)

Después de entregar el YAML funcional, incluir siempre:

```
CKA LEARNING
─────────────
Dominio:     [Cluster Architecture | Workloads | Services | Storage | Troubleshooting]
Concepto:    [Nombre del concepto K8s principal usado en esta solución]
Explicación: [2-4 oraciones explicando el "por qué" de cada decisión técnica]
Referencia:  [URL de kubernetes.io con la documentación oficial]
Tip CKA:     [Un dato práctico que suelen evaluar en el examen]
```

### Paso 5 — Registrar en HarnessDB (obligatorio)

Al finalizar, registrar en la memoria del proyecto:

```bash
# Si se tomó una decisión arquitectónica significativa:
python3 .harness/scripts/harness-write.py decision \
  --agent infrastructure \
  --domain [dominio] \
  --title "[título conciso de la decisión]" \
  --context "[por qué se tomó]" \
  --decision "[qué se decidió]" \
  --related-files "[archivos afectados]" \
  --tags "[tags relevantes]"

# Si se descubrió un gotcha o patrón importante:
python3 .harness/scripts/harness-write.py lesson \
  --agent infrastructure \
  --category [error|gotcha|pattern|tip] \
  --title "[título]" \
  --description "[descripción]" \
  --severity [info|warning|critical]

# Si se creó o modificó un recurso K8s:
python3 .harness/scripts/harness-write.py resource \
  --kind [tipo] --name [nombre] --manifest-path [ruta]

# Siempre registrar la actividad:
python3 .harness/scripts/harness-write.py activity \
  --agent infrastructure \
  --action [create|modify|validate] \
  --target "[recurso afectado]" \
  --summary "[resumen de lo que se hizo]"
```

**Criterio de registro**: No registrar todo — solo decisiones que impacten la arquitectura, lecciones que eviten futuros errores, y recursos nuevos o modificados significativamente.

---

## Contrato de Output

```
INFRASTRUCTURE PROPOSAL
───────────────────────
Archivos a crear:    [lista con rutas completas]
Archivos a modificar: [lista con rutas y secciones afectadas]
Orden de aplicación: [secuencia kubectl apply]
Advertencias:        [breaking changes, downtime esperado, etc.]
Validación sugerida: [comandos kubectl get/describe para verificar]
CKA Layer:           [dominio + concepto + explicación + referencia + tip]
```

---

## Reglas de Escalamiento

Escalo al Orquestador si:
- El cambio requiere modificar `kind-config.yaml` (implica recrear el clúster)
- El componente no tiene precedente en el repo (patrón completamente nuevo)
- El cambio involucra recursos del namespace `kube-system`
- Hay conflicto entre lo que pide el usuario y las convenciones del proyecto


## Content from infra_skill.md

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

---

## Errores Comunes (Lecciones Aprendidas de HarnessDB)

> **⚠️ PREVENCIÓN OBLIGATORIA:** Revisa esta lista antes de proponer cambios para no repetir fallos históricos del proyecto.

1. **Mismatch Selectors-Labels (Fallo Crítico de Red):** 
   - **El error:** Un `Service` no enruta tráfico a los pods y devuelve *Connection Refused*, a pesar de que los pods están `Running`.
   - **La causa:** El bloque `selector:` del Service no coincide **exactamente** con los `labels:` del PodTemplate en el Deployment.
   - **La regla:** Antes de entregar un Service + Deployment, copia el bloque `labels` del Deployment y pégalo directamente en el `selector` del Service. No los escribas dos veces.