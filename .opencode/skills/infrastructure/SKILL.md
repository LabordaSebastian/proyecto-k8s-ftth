---
name: infrastructure
description: "Use for Kubernetes manifest changes: deployments, services, configmaps, network policies, RBAC, resource limits, labels, selectors, imagePullPolicy, NodePort, namespaces, storage, metrics-server, PDBs, cronjobs, rolling updates, rollbacks. Trigger keywords: k8s, kubernetes, deployment, service, configmap, pdb, cronjob, manifest, yaml, kind, cluster, rollout, rollback, namespace, rbac, networkpolicy, resource limits, replicas, pod."
---

# Infrastructure Agent — Conocimiento de Manifiestos K8s

Carga el conocimiento de dominio leyendo los archivos fuente de Gemini:

```bash
# Lee las convenciones de infraestructura del proyecto
read .gemini/skills/infrastructure-agent/artifacts/infra_skill.md

# Lee el protocolo de operación del agente
read .gemini/skills/infrastructure-agent/artifacts/agent_protocol.md
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
