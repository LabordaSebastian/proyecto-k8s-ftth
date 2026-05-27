# Autoscaling y Optimización de Recursos

## Visión General

El proyecto implementa estrategias avanzadas de escalado de recursos para garantizar la estabilidad de los componentes bajo carga, mientras se protegen los recursos del clúster subyacente (nodos de Kind).

Actualmente, la estrategia principal se basa en el **Vertical Pod Autoscaler (VPA)**.

## Vertical Pod Autoscaler (VPA)

A diferencia del HPA (Horizontal Pod Autoscaler) que añade más réplicas de un pod, el VPA ajusta dinámicamente los **requests** y **limits** de CPU y Memoria de los pods existentes basándose en su uso real histórico.

### Componentes del VPA
El controlador de VPA no viene instalado por defecto en Kubernetes. Fue instalado desde el repositorio oficial (`kubernetes/autoscaler`) e inyecta tres componentes en el clúster:
1. **Recommender**: Analiza las métricas históricas provistas por el Metrics Server y sugiere recursos.
2. **Updater**: Evicta (mata) pods cuyos recursos actuales difieren significativamente del objetivo (`target`) recomendado.
3. **Admission Controller**: Intercepta la creación de pods (por ejemplo, después de un eviction) e inyecta los nuevos requests/limits en su especificación antes de que arranquen.

### Implementación en el Proyecto: Redis
Redis (`ftth-redis`) es el candidato ideal para el VPA porque:
- Corre como una réplica única (`replicas: 1`), por lo que escalar horizontalmente no es directo sin configurar Redis Cluster.
- Su consumo de memoria es altamente variable y depende directamente de los datos insertados en la caché.
- Adivinar sus límites estáticos es propenso a errores (provocando `OOMKilled` si es bajo, o desperdicio si es alto).

#### Configuración (`k8s/07-autoscaling/redis-vpa.yaml`)
El VPA de Redis está configurado en **updateMode: "Auto"** con las siguientes políticas de seguridad:
- `minAllowed`: 25m CPU / 32Mi Memory
- `maxAllowed`: 200m CPU / 256Mi Memory (para proteger el nodo Kind)

### Validación: Prueba de Estrés
La implementación fue validada exitosamente mediante una inyección de carga masiva:

1. Se utilizó un pod efímero con `redis-benchmark` para insertar 5 millones de llaves.
2. El Metrics Server reportó el pico de uso de RAM.
3. El **VPA Recommender** ajustó el `target` de memoria de 64Mi a 250Mi.
4. El **VPA Updater** evictó el pod de Redis (`Connection reset by peer` en el benchmark).
5. El **VPA Admission Controller** inyectó los nuevos recursos al reiniciar el pod, permitiéndole soportar la carga.
