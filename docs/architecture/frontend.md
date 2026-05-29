# Frontend — Nginx Dashboard

## Visión General

El Frontend es el único componente del clúster **accesible directamente desde el navegador del host**. Su función es servir el panel de control de la plataforma FTTH: una interfaz web estática que muestra el estado de la red de fibra óptica.

Está compuesto por dos recursos de Kubernetes que trabajan en pareja:

| Recurso | Nombre | Propósito |
|---|---|---|
| `ConfigMap` | `ftth-dashboard-html` | Almacena el HTML+CSS del dashboard |
| `Deployment` | `ftth-frontend` | Gestiona los Pods de Nginx que sirven el contenido |
| `Service` | `ftth-frontend-service` | Expone el puerto `30080` hacia el host via NodePort |

El flujo es el siguiente: el ConfigMap actúa como un disco virtual que contiene el archivo `index.html`. El Deployment monta ese "disco" en la ruta que Nginx usa como raíz web (`/usr/share/nginx/html`). Cuando el contenido del dashboard necesita cambiar, se edita únicamente el ConfigMap, **sin necesidad de reconstruir ni repush de ninguna imagen Docker**.

---

## Desglose Técnico

### ConfigMap — `frontend-configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ftth-dashboard-html
  labels:
    app: ftth-frontend
data:
  index.html: |
    <!DOCTYPE html>
    ...
```

#### ¿Por qué un ConfigMap y no un archivo dentro de la imagen?

Esta es una decisión de diseño fundamental que demuestra el principio de **separación entre configuración y código**.

Si el HTML estuviera dentro de la imagen de Docker (`COPY index.html /usr/share/nginx/html/`), cada vez que quisieras cambiar un título o un color del dashboard tendrías que:

1. Modificar el archivo local.
2. Reconstruir la imagen (`docker build`).
3. Re-inyectarla en Kind (`kind load`).
4. Forzar el re-rollout del Deployment (`kubectl rollout restart`).

Con el ConfigMap, el mismo cambio requiere únicamente:

```bash
kubectl edit configmap ftth-dashboard-html
# O con un archivo actualizado:
kubectl apply -f k8s/01-storage/frontend-configmap.yaml
```

!!! info "Cómo funciona el ConfigMap como volumen"
    Kubernetes convierte cada clave del bloque `data:` en un **archivo** dentro del directorio de montaje. En este caso, la clave `index.html` se convierte literalmente en el archivo `/usr/share/nginx/html/index.html` dentro del contenedor. Si se añadiera una clave `styles.css`, se crearía el archivo `styles.css` en el mismo directorio.

!!! warning "ConfigMaps no son Secrets"
    El contenido de un ConfigMap se almacena en texto plano en `etcd`. Nunca almacenes contraseñas, tokens de API o certificados en un ConfigMap. Para esos casos, usa un recurso `Secret`.

---

### Deployment — `frontend-deployment.yaml`

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

#### ¿Por qué `replicas: 2`?

Con dos réplicas, el Deployment garantiza **alta disponibilidad**. Si un nodo falla o un Pod entra en estado `CrashLoopBackOff`, el otro continúa sirviendo tráfico mientras el Controller Manager intenta recuperar el Pod fallido. El Service distribuye las peticiones entre ambas réplicas mediante round-robin.

!!! tip "Self-Healing en la práctica"
    Ejecuta `kubectl delete pod <nombre-del-pod-frontend>` y observa cómo el Deployment crea inmediatamente un Pod de reemplazo. Este mecanismo se llama **reconciliation loop** y es gestionado por el `kube-controller-manager`. El estado deseado (`replicas: 2`) siempre se mantiene.

#### ¿Por qué `nginx:alpine` y no `nginx:latest`?

La variante Alpine de Nginx pesa aproximadamente **23 MB** frente a los ~140 MB de la imagen base de Debian. En un entorno de laboratorio con recursos limitados (Kind sobre una PC), reducir el tamaño de las imágenes tiene un impacto directo en:

- El tiempo de arranque del Pod.
- La memoria consumida por el runtime de contenedores en el nodo.
- La superficie de ataque de seguridad (menos paquetes = menos vulnerabilidades).

#### Resource Requests y Limits explicados

```yaml
resources:
  requests:          # Lo mínimo garantizado para que el Pod arranque
    memory: "64Mi"
    cpu: "50m"       # 50 milicores = 5% de un núcleo de CPU
  limits:            # El techo que el Pod nunca puede superar
    memory: "128Mi"
    cpu: "100m"
```

**`requests`** es lo que el `kube-scheduler` usa para decidir en qué nodo colocar el Pod. Si un nodo no tiene al menos `64Mi` y `50m` libres, el Pod no se programa allí y queda en estado `Pending`.

**`limits`** es el techo que el contenedor nunca puede superar:
- Si supera el límite de **memoria**, el kernel del nodo lo termina inmediatamente con una señal `OOMKilled` (Out of Memory).
- Si supera el límite de **CPU**, el kernel simplemente lo **throttlea** (reduce su velocidad), no lo mata.

!!! warning "Pods sin limits son un riesgo operacional"
    Un Pod sin `limits` puede consumir todos los recursos del nodo, causando que otros Pods sean expulsados (`Evicted`) o que el nodo se vuelva inestable. Siempre define límites en entornos compartidos.

#### El mecanismo de montaje del volumen

La conexión entre el ConfigMap y el contenedor se establece en dos pasos dentro del spec del Pod:

**Paso 1 — Declarar el volumen** (a nivel del Pod): le dice a Kubernetes que existe un volumen llamado `html-volume` cuya fuente es el ConfigMap `ftth-dashboard-html`.

```yaml
volumes:
- name: html-volume
  configMap:
    name: ftth-dashboard-html
```

**Paso 2 — Montarlo en el contenedor**: le dice a Nginx dónde debe aparecer ese volumen dentro del sistema de archivos del contenedor.

```yaml
volumeMounts:
- name: html-volume
  mountPath: /usr/share/nginx/html
```

!!! info "¿Qué pasa con los archivos originales de Nginx?"
    El montaje **reemplaza completamente** el directorio `/usr/share/nginx/html` con el contenido del ConfigMap. Si la imagen de Nginx tenía un archivo `50x.html` en esa ruta, dejará de existir. Solo existirán los archivos definidos en el `data:` del ConfigMap.

---

## Instrucciones de Operación

### Aplicar los recursos

Aplica el ConfigMap primero para que esté disponible antes de que los Pods arranquen:

```bash
# Paso 1: Aplicar el ConfigMap
kubectl apply -f k8s/01-storage/frontend-configmap.yaml

# Paso 2: Aplicar el Deployment
kubectl apply -f k8s/02-deployments/frontend-deployment.yaml

# Paso 3: Aplicar el Service
kubectl apply -f k8s/03-services/frontend-service.yaml
```

### Verificar el estado

```bash
# Ver el estado del Deployment (READY, UP-TO-DATE, AVAILABLE)
kubectl get deployment ftth-frontend

# Ver los Pods y en qué nodo están programados
kubectl get pods -l app=ftth-frontend -o wide

# Verificar que el ConfigMap existe y tiene contenido
kubectl get configmap ftth-dashboard-html
kubectl describe configmap ftth-dashboard-html
```

### Actualizar el contenido del dashboard

Para modificar el HTML sin reconstruir la imagen:

```bash
# Editar directamente (abre el editor por defecto)
kubectl edit configmap ftth-dashboard-html

# O aplicar el archivo modificado localmente
kubectl apply -f k8s/01-storage/frontend-configmap.yaml
```

!!! tip "Propagación del cambio"
    Kubernetes propaga los cambios en el ConfigMap a los Pods que lo montan como volumen de forma eventual (en un ciclo de ~1 minuto por defecto, controlado por `--sync-frequency` del `kubelet`). Para forzar la actualización inmediata, ejecuta un rolling restart del Deployment:
    ```bash
    kubectl rollout restart deployment/ftth-frontend
    ```

### Debugging

```bash
# Ver los logs de Nginx (errores de carga de archivos, peticiones HTTP)
kubectl logs -l app=ftth-frontend --tail=50

# Entrar al contenedor para inspeccionar el sistema de archivos
kubectl exec -it deployment/ftth-frontend -- sh

# Dentro del contenedor, verificar que el archivo está montado correctamente
ls -la /usr/share/nginx/html/
cat /usr/share/nginx/html/index.html

# Ver los eventos del Deployment (útil si un Pod no arranca)
kubectl describe deployment ftth-frontend
kubectl get events --sort-by=.lastTimestamp | grep frontend
```

### Verificar el acceso externo

```bash
# Confirmar que el Service NodePort está exponiendo el puerto correcto
kubectl get service ftth-frontend-service

# Acceder desde el host
curl http://localhost:30080
```
