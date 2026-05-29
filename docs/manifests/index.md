# Manifiestos de Kubernetes

Esta sección documenta todos los recursos declarativos del clúster organizados por tipo.

Los manifiestos se encuentran bajo la carpeta `k8s/`, ordenados numéricamente para garantizar un orden de aplicación predecible:

```text
k8s/
├── 01-storage/       # ConfigMaps (contenido estático del Frontend)
├── 02-deployments/   # Workloads: Frontend, Backend, Redis, CronJob
├── 03-services/      # Exposición de red: ClusterIP y NodePort
├── 04-metrics/       # Metrics Server para kubectl top
└── 05-autoscaling/   # HPA para backend y VPA para base de datos
```

!!! tip "Orden de aplicación"
    El script `manage-env.sh` aplica los manifiestos de forma recursiva (`kubectl apply -Rf k8s/`). El orden numérico de las carpetas asegura que los ConfigMaps estén disponibles **antes** de que los Pods que los montan sean creados.

## Recursos documentados

| Tipo | Archivo | Sección |
|---|---|---|
| Deployment | `02-deployments/*.yaml` | [Deployments](deployments.md) |
| Service | `03-services/*.yaml` | [Services](services.md) |
| ConfigMap | `01-storage/frontend-configmap.yaml` | [ConfigMaps](configmaps.md) |
| DaemonSet/Deployment | `04-metrics/metrics-server.yaml` | [Metrics Server](metrics-server.md) |
| HPA / VPA | `05-autoscaling/*.yaml` | [Autoscaling](autoscaling.md) |
