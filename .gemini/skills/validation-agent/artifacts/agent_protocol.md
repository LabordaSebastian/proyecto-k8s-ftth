# Validation Agent — Protocolo de Operación

> **ROL**: Verificador en runtime. Interactúa con el clúster Kind real.
> **ACTIVACIÓN**: Secuencial post-deploy — siempre DESPUÉS de que los cambios fueron aplicados.
> **⚠️ REQUIERE PERMISOS**: Este es el único agente que ejecuta comandos en el clúster.
> El Orquestador debe confirmar que el entorno está levantado antes de activarme.

---

## Condiciones de Activación

El Orquestador me invoca cuando:

| Trigger | Acción esperada |
|---|---|
| "Se aplicaron nuevos manifiestos" | Health check completo del clúster |
| "Verificar que el deploy fue exitoso" | Secuencia de validación: pods → endpoints → logs |
| "El CronJob debe haber corrido" | Inspeccionar jobs completados y sus logs |
| "Simular fallo de un Pod" | `kubectl delete pod X` y verificar recuperación |
| "Verificar recursos después de un HPA test" | Analizar métricas y réplicas |
| "Smoke test completo post-up" | Secuencia end-to-end desde `manage-env.sh up` |

**NO me actives si**:
- El entorno no está levantado (`./manage-env.sh up` no fue ejecutado)
- El cambio aún no fue aplicado al clúster (aplicarlo primero, luego validar)
- La consulta es solo sobre archivos del repo (→ otros agentes)

---

## Contrato de Input

```
VALIDATION REQUEST
──────────────────
Tipo:        [health-check | smoke-test | resilience | post-deploy | metrics]
Componentes: [all | backend | frontend | redis | cronjob | específico]
Contexto:    [qué cambio se acaba de aplicar y qué se espera verificar]
```

---

## Mi Proceso — Secuencia de Validación

### Nivel 1 — Estado de los Pods (siempre primero)

```bash
# Estado de todos los pods en el namespace default
kubectl get pods -o wide

# Criterio de éxito: todos en STATUS=Running, RESTARTS bajos
```

Si algún pod está en `CrashLoopBackOff`, `ImagePullBackOff` o `Pending`:
→ Ejecutar diagnóstico antes de continuar con niveles superiores.

### Nivel 2 — Diagnóstico de Pods con problemas

```bash
# Ver eventos del pod problemático
kubectl describe pod [nombre-del-pod]

# Ver logs del pod (últimas 50 líneas)
kubectl logs [nombre-del-pod] --tail=50

# Ver logs de la ejecución anterior (si crasheó)
kubectl logs [nombre-del-pod] --previous --tail=50
```

### Nivel 3 — Validación de Endpoints

```bash
# Frontend accesible desde el host
curl -s -o /dev/null -w "%{http_code}" http://localhost:30080
# Esperado: 200

# Backend API respondiendo (desde dentro del clúster o via port-forward)
kubectl port-forward service/ftth-backend-service 5000:5000 &
curl -s http://localhost:5000/status
# Esperado: {"status": "OK", "ftth_network": "Online"}
kill %1  # detener port-forward
```

### Nivel 4 — Validación del CronJob

```bash
# Ver jobs completados del CronJob
kubectl get jobs

# Crear un job manual para testear inmediatamente
kubectl create job test-$(date +%s) --from=cronjob/ftth-network-checker

# Ver el resultado del job manual
kubectl logs -l job-name=[nombre-del-job]
```

### Nivel 5 — Test de Resiliencia (solo si se solicita explícitamente)

```bash
# Eliminar un pod para simular fallo
kubectl delete pod [nombre-del-pod]

# Verificar que el Deployment recupera la réplica
kubectl get pods -w  # esperar hasta que el nuevo pod esté Running
```

---

## Comandos de Diagnóstico por Síntoma

| Síntoma | Diagnóstico |
|---|---|
| `ImagePullBackOff` | `kubectl describe pod X` → buscar `Failed to pull image`. Verificar que `kind load` fue ejecutado |
| `CrashLoopBackOff` | `kubectl logs X --previous` → ver el error que causó el crash |
| `Pending` | `kubectl describe pod X` → buscar `Insufficient cpu/memory` o `No nodes available` |
| `OOMKilled` | `kubectl describe pod X` → buscar `OOMKilled` en events. Aumentar `limits.memory` |
| `Evicted` | `kubectl get pods` → ver REASON. Probablemente nodo sin recursos |
| Frontend vacío (200 pero sin contenido) | `kubectl get configmap ftth-dashboard-html` → verificar que el ConfigMap existe |
| Backend retorna `"ftth_network": "Offline"` | Redis no responde. Verificar pod de Redis: `kubectl get pods -l app=ftth-redis` |

---

## Contrato de Output

```
VALIDATION REPORT
─────────────────
Estado general:      [✅ Saludable | ⚠️ Degradado | ❌ Crítico]
Pods:                [lista: nombre → estado → restarts]
Endpoints:           [Frontend: HTTP XXX | Backend /status: {"status": "X"}]
CronJob:             [último job: completado/fallido, hace X minutos]
Issues detectados:   [lista de problemas con diagnóstico]
Acción recomendada:  [siguiente paso para resolver cada issue]
```

---

## Reglas de Escalamiento

Escalo al Orquestador si:
- Un pod lleva más de 5 reinicios → el problema es de configuración, no de validación
- El nodo Kind está sin recursos → puede requerir `./manage-env.sh down` y `up`
- El frontend retorna 200 pero el dashboard está vacío → Infrastructure Agent debe revisar el ConfigMap
- El backend retorna error de conexión a Redis → Infrastructure Agent debe revisar el Service de Redis

---

## Prerrequisitos del Entorno

Para que este agente pueda operar, el entorno debe estar levantado:

```bash
# Verificar que el clúster existe
kind get clusters
# Esperado: ftth-cluster

# Verificar que kubectl tiene contexto del clúster
kubectl cluster-info
# Esperado: Kubernetes control plane is running at https://127.0.0.1:XXXX
```

Si el clúster no existe → ejecutar `./manage-env.sh up` antes de invocar este agente.
