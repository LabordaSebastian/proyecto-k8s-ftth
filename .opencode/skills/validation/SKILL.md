---
name: validation
description: "Use for runtime validation against the live Kind cluster: health checks, pod status, endpoint verification, smoke tests, resilience tests, diagnosis of CrashLoopBackOff, ImagePullBackOff, OOMKilled, Pending pods, rollback verification, rolling update verification. Trigger keywords: validate, validation, verify, health check, smoke test, diagnosis, kubectl, cluster, runtime, pod status, endpoint, curl, port-forward, resilience, rollout status, rollback test."
---

# Validation Agent — Conocimiento de Validación en Runtime

Carga el conocimiento de dominio leyendo los archivos fuente de Gemini:

```bash
# Lee el protocolo de operación del agente
read .gemini/skills/validation-agent/artifacts/agent_protocol.md
```

El contenido de ese archivo es la fuente de verdad actualizada. Esto incluye:

- **Niveles de validación**:
  1. Estado de pods (`kubectl get pods -o wide`)
  2. Diagnóstico de pods con problemas (`kubectl describe`, `kubectl logs --previous`)
  3. Validación de endpoints (curl a frontend:30080, port-forward a backend:5000/status)
  4. Validación de CronJob (jobs completados, job manual desde cronjob)
  5. Test de resiliencia (kubectl delete pod + verificar recuperación)
- **Diagnóstico por síntoma**: ImagePullBackOff, CrashLoopBackOff, Pending, OOMKilled, Evicted
- **Comandos específicos del proyecto**: curl localhost:30080, kubectl port-forward svc/ftth-backend-service 5000:5000
- **Prerrequisitos**: clúster debe existir (`kind get clusters` → `ftth-cluster`)
