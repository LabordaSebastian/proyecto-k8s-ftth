# Conceptos Claves (CKA Cheat-Sheet)

## Visión General

Esta sección sirve como **material de repaso acelerado** orientado a la certificación **Certified Kubernetes Administrator (CKA)**. Desglosa los componentes arquitectónicos fundamentales implementados en el proyecto FTTH-K8s, explicando su rol desde la teoría oficial de Kubernetes hasta su aplicación práctica en nuestro entorno.

| Recurso | Nivel de Examen | Aplicación en el Proyecto |
|---|---|---|
| `Deployment` | Fundamental | Gestión de Backend, Frontend y Redis |
| `Service` | Fundamental | Red interna (ClusterIP) y externa (NodePort) |
| `Probes` | Intermedio | Health checks del Backend (`/health`) |
| `CronJob` | Fundamental | Tarea de monitoreo de red (`ftth-network-checker`) |
| `ConfigMap` | Fundamental | Inyección del código estático del Frontend |
| `Volumes` | Fundamental | Montaje del ConfigMap dentro del Nginx |
| `Requests & Limits` | Avanzado (Scheduling) | QoS y prevención de OOMKilled/Throttling |
| `Affinity & Taints` | Avanzado (Scheduling) | Control estricto de en qué nodo cae Redis y Kubeview |

---

## Desglose Técnico de Conceptos

### 1. Deployments y Rolling Updates

- **¿Qué es?** Un controlador de Kubernetes que proporciona actualizaciones declarativas para Pods y ReplicaSets.
- **¿Para qué sirve?** Garantiza que el número deseado de Pods esté siempre en ejecución. Si un nodo falla, el Deployment levanta los Pods en un nodo sano. Además, gestiona transiciones seguras entre versiones.
- **Caso de uso en el proyecto:** `ftth-backend-deployment` declara `replicas: 2`. Utiliza la estrategia `RollingUpdate` con `maxSurge: 1` y `maxUnavailable: 0`, lo que significa que durante una actualización (ej. cambio de imagen a `v2`), Kubernetes creará un pod nuevo antes de destruir los viejos, garantizando cero *downtime*.

### 2. Services: ClusterIP vs NodePort

- **¿Qué es?** Una abstracción que define un conjunto lógico de Pods y una política de red para acceder a ellos. Desacopla la red dinámica de los Pods (que cambian de IP al reiniciarse) ofreciendo un DNS o IP estable.
- **¿Para qué sirve?**
  - **`ClusterIP` (Por defecto):** Expone el servicio solo dentro del clúster K8s.
  - **`NodePort`:** Abre un puerto estático (rango 30000-32767) en todos los nodos trabajadores, permitiendo tráfico desde fuera del clúster.
- **Caso de uso en el proyecto:** 
  - El Redis y el Backend utilizan `ClusterIP` porque son bases de datos y APIs internas (el usuario final nunca debería golpear la base de datos directamente).
  - El Frontend utiliza `NodePort: 30080` para que puedas acceder al dashboard desde el navegador de tu computadora anfitriona (`http://localhost:30080`).

### 3. Liveness, Readiness y PreStop Hooks

- **¿Qué son?** Diagnósticos (Probes) y eventos de ciclo de vida ejecutados periódicamente por el Kubelet en cada nodo.
- **¿Para qué sirven?**
  - **`ReadinessProbe`:** Le dice al `Service` cuándo el Pod está listo para recibir tráfico web.
  - **`LivenessProbe`:** Le dice al `Kubelet` cuándo la aplicación se colgó (deadlock) y necesita que se reinicie el contenedor.
  - **`PreStop Hook`:** Ejecuta un comando antes de enviar el `SIGTERM` al Pod, permitiendo cierres gráciles (graceful shutdown).
- **Caso de uso en el proyecto:** En el Backend, apuntamos `httpGet` a `/health` por el puerto 5000. Si la DB (Redis) se cae y el Backend no puede operar, el *readiness probe* fallará, sacando al pod del *Load Balancer* del Service temporalmente, pero sin reiniciarlo a la fuerza.

### 4. ConfigMaps (CM)

- **¿Qué es?** Un objeto de la API usado para almacenar datos no confidenciales en formato clave-valor.
- **¿Para qué sirve?** Para desacoplar la configuración específica del entorno de la imagen del contenedor, permitiendo que las imágenes sean portátiles (Doce Factores / Twelve-Factor App).
- **Caso de uso en el proyecto:** El archivo estático `index.html` del frontend completo se almacena como un ConfigMap (`frontend-configmap.yaml`) y se inyecta vía `volumeMount` directo al Nginx. Esto permite editar el diseño del dashboard y aplicarlo con `kubectl apply` sin tener que hacer `docker build` de la imagen del Nginx.

### 5. CronJobs

- **¿Qué es?** Un controlador que crea `Jobs` (trabajos finitos) en un horario programado similar al formato `cron` de Linux.
- **¿Para qué sirve?** Backups de bases de datos, envíos de emails en lote, o monitoreo periódico. A diferencia de un Pod normal, se espera que el contenedor muera (termine) exitosamente una vez finalizada la tarea.
- **Caso de uso en el proyecto:** `ftth-network-checker` se activa cada 2 minutos (`*/2 * * * *`). Levanta un contenedor ligero (BusyBox), ejecuta un `wget` contra el backend, y muere. La regla `restartPolicy: OnFailure` asegura que el Pod no se reinicie a menos que el script devuelva un código de error.

### 6. Resource Requests y Limits

- **¿Qué son?** Parámetros de Quality of Service (QoS). 
  - `Requests`: Lo que el scheduler garantiza que el nodo tiene disponible antes de ubicar el pod.
  - `Limits`: El límite máximo que el contenedor puede consumir.
- **¿Para qué sirven?** Proteger los recursos del nodo (CPU/Memoria).
  - Si un pod excede su límite de Memoria → Es asesinado por el kernel del nodo (`OOMKilled`).
  - Si un pod excede su límite de CPU → Su ejecución es ralentizada (`Throttled`), pero no muere.
- **Caso de uso en el proyecto:** Cada componente tiene estos parámetros definidos. Por ejemplo, la imagen pesada del Python API requiere como mínimo `64Mi` de RAM, pero nunca se le permitirá usar más de `128Mi` (en cuyo caso sería terminado para evitar que afecte al Nginx o Redis del mismo nodo).

### 7. imagePullPolicy

- **¿Qué es?** Política de Kubelet sobre cuándo contactar al registry de contenedores (Docker Hub, ECR, etc.).
- **¿Para qué sirve?** Las opciones son `Always`, `IfNotPresent` o `Never`.
- **Caso de uso en el proyecto:** Dado que usamos un clúster local (Kind), construimos la imagen de Python localmente. Si K8s intentara buscar `ftth-backend:v1` en Docker Hub, fallaría (`ImagePullBackOff`). Usar `imagePullPolicy: Never` le ordena explícitamente usar la imagen en caché del nodo.

### 8. Node Affinity y Node Selectors

- **¿Qué es?** Reglas de *scheduling* que atraen los Pods hacia Nodos específicos basados en las etiquetas (labels) del Nodo.
- **¿Para qué sirve?** Asegurar que ciertas cargas de trabajo (ej. bases de datos, procesamiento GPU) caigan en los servidores físicos correctos.
- **Caso de uso en el proyecto:** En `redis-deployment.yaml`, usamos `nodeAffinity` exigiendo que el nodo destino tenga el label `role=database` (`requiredDuringSchedulingIgnoredDuringExecution`). Si ningún nodo cumple, el Pod de Redis se quedará en estado `Pending`.

### 9. Taints y Tolerations

- **¿Qué son?** El opuesto a la Afinidad. Un *Taint* repele a los Pods de un Nodo. Un *Toleration* le permite a un Pod ignorar esa repulsión.
- **¿Para qué sirve?** Dedicar Nodos enteros a usos exclusivos (ej. Nodos del Control Plane que repelen cargas de usuario).
- **Caso de uso en el proyecto:** Aunque la infraestructura *core* no impone taints estrictos, la herramienta externa que instalamos (`kubeview`) está configurada vía Helm (`values.yaml`) para aceptar un array de `tolerations: []`. Esto es clave en CKA: si querés que Kubeview corra en el Control Plane, tendrías que pasarle el *toleration* para ignorar el taint por defecto `node-role.kubernetes.io/control-plane:NoSchedule`.

### 10. Relación Deployment -> ReplicaSet -> Pod

- **¿Qué es?** La jerarquía de controladores en Kubernetes.
- **¿Para qué sirve?** El usuario casi nunca crea `Pods` directamente. Crea `Deployments`.
- **Caso de uso en el proyecto:** Cuando aplicamos `backend-deployment.yaml`, el objeto `Deployment` crea y gestiona un objeto `ReplicaSet` de forma transparente. Este ReplicaSet es el que realmente asegura que haya 2 réplicas del Pod corriendo. Si inspeccionás con `kubectl get rs`, verás objetos con nombres como `ftth-backend-6d8b4c95f` (donde el sufijo alfanumérico representa el hash del template de ese despliegue).

### 11. Volumes y VolumeMounts

- **¿Qué son?** Abstracciones de almacenamiento atadas al ciclo de vida del Pod (o más persistentes si usamos PVs/PVCs).
- **¿Para qué sirven?** Montar archivos, directorios, o proveer almacenamiento persistente dentro del sistema de archivos efímero del contenedor.
- **Caso de uso en el proyecto:** En el `frontend-deployment.yaml` declaramos un volumen de tipo `configMap` llamado `html-volume`. Luego, usamos `volumeMounts` para mapear ese volumen sobre la ruta `/usr/share/nginx/html/` dentro del pod Nginx, pisando el index.html original.

---

!!! tip "Consejo CKA: Resolución de Problemas"
    Durante el examen, si un servicio no resuelve, revisá siempre las tres capas en este orden: **1.** ¿Están los Pods en estado `Running` y `Ready`? (`kubectl get pods`), **2.** ¿Coinciden los `matchLabels` del Service con los del Pod? (`kubectl get endpoints`), **3.** ¿Las NetworkPolicies están bloqueando el tráfico?
