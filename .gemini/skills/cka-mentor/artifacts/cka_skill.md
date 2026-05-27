# Skill: Conocimiento CKA para el Proyecto FTTH-K8s

> **ROL**: Knowledge base del **CKA Mentor**.
> Contiene los 5 dominios del examen CKA con sus conceptos, pesos y
> relación con los recursos implementados en el proyecto FTTH.
> El protocolo de operación está en:
> `.gemini/skills/cka-mentor/artifacts/agent_protocol.md`

---

## 1. Dominios del Examen CKA (2024-2025)

| # | Dominio | Peso | Implementado en FTTH |
|---|---|---|---|
| 1 | Cluster Architecture, Installation & Configuration | 25% | `kind-config.yaml`, RBAC (pendiente) |
| 2 | Workloads & Scheduling | 15% | Deployments, CronJob, affinity, resources |
| 3 | Services & Networking | 20% | ClusterIP, NodePort, DNS interno |
| 4 | Storage | 10% | ConfigMap como volumen |
| 5 | Troubleshooting | 30% | Validation Agent cubre este dominio |

---

## 2. Dominio 1: Cluster Architecture (25%)

### Conceptos clave
- **RBAC**: Role, ClusterRole, RoleBinding, ClusterRoleBinding
- **etcd**: Backup con `etcdctl snapshot save`, restore con `etcdctl snapshot restore`
- **kubeadm**: `kubeadm upgrade plan`, `kubeadm upgrade apply`
- **HA**: Múltiples control planes, etcd stacked vs external

### Implementado en el proyecto
- `kind-config.yaml`: Clúster de 2 nodos (1 control-plane + 1 worker)
- `k8s/01-namespaces-rbac/`: Directorio preparado para manifiestos RBAC

### Comandos imperativos rápidos
```bash
# Crear un Role
kubectl create role pod-reader --verb=get,list,watch --resource=pods

# Crear un RoleBinding
kubectl create rolebinding read-pods --role=pod-reader --user=jane

# Backup etcd
ETCDCTL_API=3 etcdctl snapshot save /tmp/backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

---

## 3. Dominio 2: Workloads & Scheduling (15%)

### Conceptos clave
- **Deployment**: Gestión declarativa de ReplicaSets y Pods
- **ReplicaSet**: Garantiza N réplicas de un Pod (gestionado por Deployment)
- **DaemonSet**: Un Pod por nodo (monitoreo, logging)
- **StatefulSet**: Pods con identidad estable y almacenamiento persistente
- **CronJob/Job**: Tareas finitas programadas
- **Affinity/Anti-Affinity**: Control de scheduling por labels de nodo
- **Taints/Tolerations**: Repulsión de pods desde nodos
- **Resource Requests/Limits**: QoS y scheduling del kube-scheduler

### Implementado en el proyecto
- `k8s/03-deployments/backend-deployment.yaml`: RollingUpdate, replicas, probes, preStop, resources
- `k8s/03-deployments/redis-deployment.yaml`: nodeAffinity (`role=database`)
- `k8s/03-deployments/network-checker-cronjob.yaml`: CronJob con BusyBox

### Comandos imperativos rápidos
```bash
# Crear un Deployment rápido
kubectl create deployment nginx --image=nginx:alpine --replicas=3

# Escalar réplicas
kubectl scale deployment nginx --replicas=5

# Ver historial de rollouts
kubectl rollout history deployment/ftth-backend

# Rollback a la revisión anterior
kubectl rollout undo deployment/ftth-backend

# Agregar label a un nodo (para affinity)
kubectl label nodes ftth-cluster-worker role=database
```

---

## 4. Dominio 3: Services & Networking (20%)

### Conceptos clave
- **ClusterIP**: Acceso interno, IP virtual estable
- **NodePort**: Expone en puerto del nodo (30000-32767)
- **LoadBalancer**: Requiere cloud provider
- **ExternalName**: Alias DNS a servicio externo
- **Ingress**: Enrutamiento HTTP/HTTPS basado en host/path
- **NetworkPolicy**: Firewall a nivel pod (ingress/egress)
- **CoreDNS**: Resolución interna `<service>.<namespace>.svc.cluster.local`

### Implementado en el proyecto
- `k8s/05-services/backend-service.yaml`: ClusterIP (solo acceso interno)
- `k8s/05-services/frontend-service.yaml`: NodePort 30080
- `k8s/05-services/redis-service.yaml`: ClusterIP (aislado)
- DNS: El backend resuelve `ftth-redis-service` vía CoreDNS automáticamente

### Comandos imperativos rápidos
```bash
# Crear un Service ClusterIP
kubectl expose deployment nginx --port=80 --target-port=80

# Crear un Service NodePort
kubectl expose deployment nginx --port=80 --type=NodePort

# Verificar endpoints de un Service
kubectl get endpoints ftth-backend-service

# Verificar resolución DNS dentro del clúster
kubectl run test-dns --image=busybox:latest --rm -it -- nslookup ftth-backend-service

# Crear una NetworkPolicy básica
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF
```

---

## 5. Dominio 4: Storage (10%)

### Conceptos clave
- **PersistentVolume (PV)**: El "disco" provisionado por el admin
- **PersistentVolumeClaim (PVC)**: El "pedido" del usuario/pod
- **StorageClass**: Provisioning dinámico
- **accessModes**: ReadWriteOnce (RWO), ReadOnlyMany (ROX), ReadWriteMany (RWX)
- **Volume types**: emptyDir, hostPath, configMap, secret, nfs

### Implementado en el proyecto
- `k8s/02-storage/frontend-configmap.yaml`: ConfigMap montado como volumen
- `k8s/03-deployments/frontend-deployment.yaml`: `volumeMounts` + `volumes` (configMap → Nginx)

### Comandos imperativos rápidos
```bash
# Crear un PV
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /data/my-pv
EOF

# Crear un PVC
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

# Verificar binding
kubectl get pv,pvc
```

---

## 6. Dominio 5: Troubleshooting (30%)

### Conceptos clave
- **Pod failures**: CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled
- **Node failures**: NotReady, SchedulingDisabled, disk/memory pressure
- **Network issues**: DNS resolution, Service endpoints vacíos, NetworkPolicy bloqueante
- **Control plane**: kube-apiserver, kube-scheduler, kube-controller-manager, etcd
- **Logging**: `kubectl logs`, `kubectl describe`, `kubectl get events`

### Implementado en el proyecto
- Validation Agent: Protocolo de 5 niveles de diagnóstico
- Probes: readinessProbe y livenessProbe en el backend
- Resources: requests/limits en todos los componentes (previene OOMKilled)

### Comandos de diagnóstico rápidos
```bash
# Ver estado de todos los pods
kubectl get pods -A -o wide

# Eventos ordenados por tiempo
kubectl get events --sort-by=.lastTimestamp

# Logs de un pod con crash
kubectl logs <pod> --previous --tail=50

# Describir un pod para ver eventos
kubectl describe pod <pod>

# Verificar estado del nodo
kubectl describe node <node> | grep -A 5 Conditions

# Verificar componentes del control plane
kubectl get componentstatuses  # deprecated pero útil
kubectl -n kube-system get pods

# Debug de DNS
kubectl run debug --image=busybox:latest --rm -it -- nslookup kubernetes.default

# Verificar que un Service tiene endpoints
kubectl get endpoints <service>
```

---

## 7. Reglas para el CKA Mentor

1. **Fuente de verdad**: Solo `kubernetes.io/docs`. No citar blogs, StackOverflow ni herramientas de terceros.
2. **Idioma**: Explicaciones en español. Nombres de recursos K8s en inglés.
3. **Conexión con el proyecto**: Siempre que un concepto esté implementado en FTTH, mencionarlo como ejemplo real.
4. **Comandos imperativos**: Para cada concepto, incluir el comando `kubectl` imperativo rápido (velocidad en el examen).
5. **No inventar**: Si un concepto no está cubierto por la documentación oficial, decirlo explícitamente.
