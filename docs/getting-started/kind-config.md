# Configuración de la Infraestructura (kind-config.yaml)

**[Kind (Kubernetes IN Docker)](https://kind.sigs.k8s.io/)** es una herramienta que nos permite correr clústeres locales usando contenedores de Docker como "nodos". Nuestro archivo `kind-config.yaml` le indica a Kind exactamente cómo debe crear la topología de nuestro clúster.

Puedes copiar este archivo directamente:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ftth-cluster
nodes:
  - role: control-plane
    extraPortMappings:
    - containerPort: 30080
      hostPort: 30080
      protocol: TCP
    - containerPort: 30088  # KubeView - visualización del clúster
      hostPort: 30088
      protocol: TCP
  - role: worker
    labels:
      role: database
      disktype: ssd
```

### Explicación sección por sección:

1. **`kind: Cluster` y `apiVersion`**: Declara el tipo de recurso y la versión de la API que Kind necesita para leer este archivo.
2. **`name: ftth-cluster`**: Le asigna un nombre personalizado a nuestro clúster (por defecto se llamaría `kind`).
3. **`nodes:`**: Aquí definimos la arquitectura física (nodos) de nuestro clúster.
    * **Nodo 1 (`role: control-plane`)**: Este es el cerebro del clúster (Master node). Contiene la API Server, etcd, scheduler, etc.
        * **`extraPortMappings`**: Esto es **clave**. Como el clúster corre dentro de Docker, necesitamos mapear puertos desde nuestra computadora anfitriona hacia los nodos para poder acceder a nuestras aplicaciones desde el navegador.
        * **`30080`**: Exponemos el Frontend (Dashboard de FTTH).
        * **`30088`**: Exponemos KubeView (Herramienta visual del clúster).
    * **Nodo 2 (`role: worker`)**: Este es un nodo esclavo donde correrán nuestros Pods.
        * **`labels`**: (Etiquetas). Le asignamos la etiqueta `role: database` y `disktype: ssd`. Esto es un concepto fundamental del CKA: nos permite practicar **Node Affinity / Node Selectors**, forzando por ejemplo a que el Pod de nuestra base de datos (Redis) se instale *exclusivamente* en este nodo.
