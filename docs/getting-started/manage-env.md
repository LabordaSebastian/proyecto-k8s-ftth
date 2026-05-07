# Automatización del Ciclo de Vida (manage-env.sh)

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
