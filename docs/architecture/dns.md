# Servidor DNS Custom (CoreDNS)

## Visión General

El servidor DNS de FTTH se despliega como un componente dedicado para resolver zonas privadas (por ejemplo, `ftth.local`) sin interferir con el CoreDNS nativo del clúster (`kube-system`). Su objetivo principal es permitir la resolución de nombres internos customizados y facilitar simulaciones o pruebas desde fuera del clúster.

!!! warning "Aviso de Arquitectura a Futuro"
    Actualmente, este servicio expone directamente el puerto UDP/TCP 53 mediante la funcionalidad de **NodePort** (mapeando un puerto directamente hacia el host físico). 
    Se ha planificado una evolución en la arquitectura: **esta configuración posiblemente será sustituida por la implementación de Gateway API** (o un Ingress Controller compatible con UDP). Al migrar a Gateway API, el DNS quedará puramente interno (`ClusterIP`) y el Gateway será el encargado nativo de enrutar el tráfico L4 (usando `UDPRoute`) de forma más robusta y escalable.

## Manifiestos Involucrados

1. **ConfigMap (`k8s/02-storage/dns-configmap.yaml`)**
   Contiene el `Corefile`, que es el archivo principal de configuración de CoreDNS. Aquí declaramos la zona privada y los registros A locales.
2. **Deployment (`k8s/03-deployments/dns-deployment.yaml`)**
   El workload que ejecuta la imagen `coredns/coredns:1.11.1`. Carga su configuración montando el ConfigMap como un volumen de datos.
3. **Service (`k8s/05-services/dns-service.yaml`)**
   Expone el puerto 53 del pod hacia el exterior mediante `NodePort: 30053`.

## Deep Dive CKA: NodePort y ConfigMaps

El examen CKA evalúa fuertemente el acoplamiento de configuración (volúmenes de tipo `configMap`) y la exposición de servicios:

- **Desacople de Configuración:** En lugar de crear una imagen Docker personalizada con el `Corefile` (lo que requeriría recompilar la imagen por cada cambio de registro DNS), inyectamos la configuración como un volumen en tiempo de ejecución (`volumeMounts`). Si actualizas el ConfigMap, el archivo cambia dinámicamente en el pod.
- **Service NodePort:** A diferencia de `ClusterIP` que solo es accesible dentro de la red virtual de Kubernetes, un `NodePort` le indica al componente `kube-proxy` en cada nodo del clúster que abra un puerto físico específico (en nuestro caso, 30053) y envíe todo el tráfico recibido allí hacia el `targetPort` del pod.

> **Tip:** Para el troubleshooting de un NodePort, siempre debes comprobar:
> 1. Que el `selector` del Service haga match exacto con los `labels` del Pod.
> 2. Que el nodo anfitrión tenga ese puerto realmente abierto (no bloqueado por firewalls locales).
