# Autoscaling — Manifiestos HPA y VPA

Esta sección documenta los recursos de autoscaling ubicados en `k8s/05-autoscaling/`. Son los mecanismos que ajustan automáticamente los recursos del clúster para adaptarse a la carga real de trabajo.

## Visión General

| Recurso | Archivo | Tipo | Target |
|---|---|---|---|
| `ftth-backend-hpa` | `k8s/05-autoscaling/backend-hpa.yaml` | HorizontalPodAutoscaler | `Deployment/ftth-backend` |
| `ftth-redis-vpa` | `k8s/05-autoscaling/redis-vpa.yaml` | VerticalPodAutoscaler | `Deployment/ftth-redis` |

---

## Artefacto — `k8s/05-autoscaling/backend-hpa.yaml`

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ftth-backend-hpa
  labels:
    app: ftth-backend
    tier: backend
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ftth-backend
  minReplicas: 2
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### ¿Por qué `autoscaling/v2` y no `v1`?

La API `v2` permite definir múltiples métricas simultáneamente (CPU, memoria, métricas custom) y usar targets de tipo `Utilization` o `AverageValue`. La `v1` solo soporta CPU con un porcentaje único.

#### ¿Por qué `minReplicas: 2`?

Garantiza **alta disponibilidad** constante. Incluso en momentos de carga mínima, siempre hay al menos 2 pods atendiendo peticiones. Si uno muere, el otro sigue sirviendo mientras el ReplicaSet lo regenera.

#### ¿Por qué `averageUtilization: 70`?

El umbral del 70% deja un margen de headroom del 30%. Esto evita que los pods se saturen antes de que el HPA tenga tiempo de crear nuevas réplicas (el escalado no es instantáneo).

---

## Artefacto — `k8s/05-autoscaling/redis-vpa.yaml`

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: ftth-redis-vpa
  labels:
    app: ftth-redis
    tier: database
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ftth-redis
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: redis-cache
      minAllowed:
        cpu: "25m"
        memory: "32Mi"
      maxAllowed:
        cpu: "200m"
        memory: "256Mi"
      controlledResources: ["cpu", "memory"]
```

#### ¿Por qué VPA para Redis y no HPA?

Redis es una base de datos **en memoria con estado** (`stateful`). Escalar horizontalmente requeriría configurar Redis Cluster, añadiendo complejidad innecesaria para un entorno de desarrollo. El VPA es la solución ideal: ajusta los recursos de un único pod según su consumo real.

#### ¿Por qué `updateMode: "Auto"`?

En modo `Auto`, el VPA evicta (mata) el pod cuando detecta que los recursos asignados difieren significativamente de los recomendados, y el Admission Controller inyecta los nuevos valores al recrearse. Esto garantiza que Redis siempre tenga los recursos óptimos sin intervención manual.

#### ¿Por qué definir `minAllowed` y `maxAllowed`?

Sin estos límites, el VPA podría recomendar valores absurdos (ej. 10Gi de RAM para un caché simple). El `maxAllowed` protege los nodos del clúster Kind (que tienen recursos limitados), mientras que el `minAllowed` asegura que Redis tenga lo mínimo para arrancar.

---

## Instrucciones de Operación

### Aplicar los recursos

```bash
kubectl apply -f k8s/05-autoscaling/
```

!!! warning "Prerequisito: VPA Controller"
    El HPA viene integrado en Kubernetes, pero el VPA **no**. El controlador del VPA se instala automáticamente en el `Paso 3/6` del script `manage-env.sh` usando el chart de Helm de Fairwinds (`fairwinds-stable/vpa`). Si aplicas el manifiesto del VPA sin el controlador instalado, obtendrás un error de CRD desconocido.

### Verificar el estado

```bash
# Ver estado del HPA (réplicas actuales vs. deseadas)
kubectl get hpa

# Ver recomendaciones del VPA
kubectl describe vpa ftth-redis-vpa

# Ver métricas en tiempo real
kubectl top pods
```

### Debugging

!!! warning "Síntoma: HPA muestra `<unknown>` en la columna TARGETS"
    Esto significa que el Metrics Server no está reportando métricas de CPU. Verificar:
    1. Que el Metrics Server está corriendo: `kubectl get pods -n kube-system | grep metrics`
    2. Que el Deployment del backend tiene `resources.requests.cpu` definido (sin esto, el HPA no puede calcular porcentajes).
