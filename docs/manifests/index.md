# Manifiestos de Kubernetes

Esta sección documenta todos los recursos declarativos del clúster organizados por tipo.

Los manifiestos se encuentran bajo la carpeta `k8s/`, ordenados numéricamente para garantizar un orden de aplicación predecible:

```text
k8s/
├── 02-storage/       # ConfigMaps (contenido estático del Frontend)
├── 03-deployments/   # Workloads: Frontend, Backend, Redis, CronJob
├── 05-services/      # Exposición de red: ClusterIP y NodePort
└── 06-metrics/       # Metrics Server para kubectl top
```

!!! tip "Orden de aplicación"
    El script `manage-env.sh` aplica los manifiestos de forma recursiva (`kubectl apply -Rf k8s/`). El orden numérico de las carpetas asegura que los ConfigMaps estén disponibles **antes** de que los Pods que los montan sean creados.

## Recursos documentados

| Tipo | Archivo | Sección |
|---|---|---|
| Deployment | `03-deployments/*.yaml` | [Deployments](deployments.md) |
| Service | `05-services/*.yaml` | [Services](services.md) |
| ConfigMap | `02-storage/frontend-configmap.yaml` | [ConfigMaps](configmaps.md) |
| DaemonSet/Deployment | `06-metrics/metrics-server.yaml` | [Metrics Server](metrics-server.md) |
