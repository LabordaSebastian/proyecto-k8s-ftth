# Pipeline de Despliegue Local (ci-cd.yml)

Este flujo simula una canalización de **Integración y Despliegue Continuos (CI/CD)**. Se ejecuta en el **Runner local** (levantado por `manage-env.sh`), no en los servidores de GitHub.

```yaml
name: FTTH CI/CD Pipeline

# 1. Disparador (Trigger)
on:
  push:
    branches:
      - main

jobs:
  build-and-deploy:
    # 2. Entorno de Ejecución
    runs-on: self-hosted 

    steps:
    # 3. Checkout del código
    - name: 📥 Obtener el código fuente
      uses: actions/checkout@v4

    # 4. Versionado automático
    - name: 🏷️ Calcular versión de imagen
      id: version
      run: |
        LATEST_TAG=$(git tag -l 'v*' --sort=-version:refname --merged 2>/dev/null | head -1)
        if [[ -z "$LATEST_TAG" ]]; then
          NEW_VERSION="v1"
        else
          VERSION_NUMBER=$(echo "$LATEST_TAG" | sed 's/v//')
          NEW_VERSION="v$((VERSION_NUMBER + 1))"
        fi
        echo "version=${NEW_VERSION}" >> $GITHUB_OUTPUT
        echo "Building image with tag: ${NEW_VERSION}"

    # 5. Construcción + dual tagging
    - name: 🔨 Construir imagen de Backend con versión
      run: |
        docker build -t ftth-backend:${{ steps.version.outputs.version }} ./src/backend
        docker tag ftth-backend:${{ steps.version.outputs.version }} ftth-backend:latest

    # 6. Inyección en el clúster Kind
    - name: 🚀 Cargar imagen en el clúster Kind
      run: |
        kind load docker-image ftth-backend:${{ steps.version.outputs.version }} --name ftth-cluster
        kind load docker-image ftth-backend:latest --name ftth-cluster

    # 7. Despliegue en Kubernetes
    - name: ☸️ Aplicar manifiestos de Kubernetes
      run: |
        kubectl apply -R -f k8s/

    # 8. Post-deploy validation
    - name: ⏳ Validar que deployments están ready
      run: |
        echo "Esperando a que los deployments estén listos..."
        kubectl rollout status deployment/ftth-backend --timeout=5m
        kubectl rollout status deployment/ftth-frontend --timeout=5m
        echo "✅ Todos los deployments están ready"

    # 9. Verificación final
    - name: ✅ Verificar estado final
      run: |
        echo "Estado actual de los Pods:"
        kubectl get pods
```

### Explicación sección por sección:

1. **`on: push: branches: [main]`**: Gatillo. El pipeline se dispara automáticamente al hacer `git push` a `main`.
2. **`runs-on: self-hosted`**: Configuración clave. Le dice a GitHub que ejecute los comandos en tu PC, no en sus servidores.
3. **Checkout**: Descarga el código fuente desde GitHub al Runner local.
4. **Versionado automático**: Calcula el próximo tag de imagen basándose en los tags de git existentes. Si el último tag es `v2`, la nueva imagen se etiqueta como `v3`. En la primera ejecución (sin tags), usa `v1`.
5. **Construcción + dual tagging**: Construye la imagen con el tag semántico (`ftth-backend:v3`) y también la etiqueta como `:latest` para mantener compatibilidad con el manifiesto del Deployment.
6. **Inyección en Kind**: Carga ambas etiquetas en los nodos del clúster Kind. Sin este paso, las imágenes locales no serían accesibles.
7. **Despliegue en Kubernetes**: Aplica todos los manifiestos de forma recursiva con `kubectl apply -R -f k8s/`, asegurando que toda la infraestructura (storage, deployments, services, metrics y autoscaling) se despliegue en un solo comando.
8. **Post-deploy validation**: Usa `kubectl rollout status` para esperar hasta que los Deployments estén completamente listos (timeout de 5 minutos). Si el rollout falla, el pipeline se marca como fallido. Esto garantiza que no se despliegue una versión rota.
9. **Verificación final**: Imprime el estado de todos los Pods como resumen en los logs.

### ¿Por qué versionado semántico con git tags?

| Beneficio | Descripción |
|---|---|
| **Trazabilidad** | Cada versión de imagen se corresponde con un commit y un tag de git |
| **Rollback** | Se puede revertir a una versión anterior directamente por tag |
| **Historial** | `kubectl rollout history` muestra el change-cause con el tag usado |
| **Consistencia** | El tag en el Deployment (ej: `ftth-backend:v3`) coincide con el tag de git |

### ¿Por qué dual tagging (`vX` + `latest`)?

`latest` permite que el manifiesto `backend-deployment.yaml` (que referencia `ftth-backend:v1`) funcione sin cambios para el primer despliegue local. El tag semántico (`vX`) proporciona trazabilidad para rolling updates en CI/CD. En producción, solo se usaría el tag semántico.
