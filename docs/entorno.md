# Aprovisionamiento del Entorno Local

Para practicar y preparar el examen CKA, necesitamos un clúster de Kubernetes donde podamos experimentar de forma rápida y segura. Para esto, utilizamos dos archivos fundamentales en nuestro proyecto: `kind-config.yaml` y `manage-env.sh`.

---

## 1. Configuración de la Infraestructura (`kind-config.yaml`)

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

---

## 2. Automatización del Ciclo de Vida (`manage-env.sh`)

Crear el clúster, compilar nuestras imágenes de Docker locales, inyectarlas en los nodos y aplicar los manifiestos YAML toma mucho tiempo si se hace a mano. 

Para eso, creé el script bash `manage-env.sh`. Actúa como un orquestador total de nuestro entorno de pruebas.

```bash
# Para levantar todo el entorno desde cero:
./manage-env.sh up

# Para destruir todo y dejar la PC limpia:
./manage-env.sh down
```

### ¿Qué hace internamente este script?

Cuando ejecutas la opción `up`, el script realiza los siguientes pasos de forma secuencial y con validaciones de errores:

1. **Validación:** Comprueba que Docker esté corriendo y que `kind`, `kubectl` y `helm` estén instalados.
2. **Creación del Clúster:** Lee el archivo `kind-config.yaml` y levanta el clúster si no existe.
3. **Compilación de Imágenes (Evitando ErrImageNeverPull):** Construye la imagen de nuestro Backend de Python de forma local y **muy importante**, utiliza `kind load docker-image` para inyectar la imagen dentro de los nodos. Si no hiciéramos esto, Kubernetes intentaría descargar la imagen de internet y fallaría.
4. **Despliegue de Manifiestos:** Ejecuta `kubectl apply` recursivamente en toda nuestra carpeta `k8s/` para levantar pods, servicios, cronjobs, etc.
5. **Herramientas Extra:** Instala KubeView (vía Helm) y Metrics Server.
6. **Agente CI/CD:** Levanta un proceso en segundo plano (background) para registrar un GitHub Actions Runner local, permitiendo simular pipelines de CI/CD.

Cuando ejecutas la opción `down`, el script inteligentemente lee el archivo `.runner.pid` para matar el proceso del GitHub Runner en segundo plano de forma limpia, y luego le ordena a Kind destruir todo el clúster, liberando los recursos de la computadora.
