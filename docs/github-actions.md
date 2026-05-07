# Flujos de GitHub Actions (CI/CD)

En este proyecto utilizamos **GitHub Actions** para automatizar tareas rutinarias. Contamos con dos flujos (workflows) principales, ubicados dentro de la carpeta `.github/workflows/`.

Uno se encarga de desplegar nuestra aplicación en el clúster local, y el otro publica automáticamente esta documentación en internet.

---

## 1. Pipeline de Despliegue Local (`ci-cd.yml`)

Este flujo simula una canalización de **Integración y Despliegue Continuos (CI/CD)**. La magia de este flujo es que no se ejecuta en los servidores en la nube de GitHub, sino que se conecta a nuestro **Runner local** (que levantamos con nuestro script `manage-env.sh`) y ejecuta los comandos directamente en nuestra PC.

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

    # 4. Construcción de la Imagen
    - name: 🔨 Construir imagen de Backend localmente
      run: |
        echo "Construyendo la imagen de Docker..."
        docker build -t ftth-backend:latest ./src/backend

    # 5. Inyección en el clúster Kind
    - name: 🚀 Cargar imagen en el clúster Kind
      run: |
        echo "Inyectando la imagen en los nodos de Kubernetes..."
        kind load docker-image ftth-backend:latest --name ftth-cluster

    # 6. Despliegue en Kubernetes
    - name: ☸️ Aplicar manifiestos de Kubernetes
      run: |
        echo "Desplegando la infraestructura declarativa..."
        kubectl apply -f k8s/01-namespaces-rbac/ || true
        kubectl apply -f k8s/02-storage/
        kubectl apply -f k8s/03-deployments/
        kubectl apply -f k8s/05-services/

    # 7. Verificación
    - name: ✅ Verificar estado
      run: |
        echo "Estado actual de los Pods:"
        kubectl get pods
```

### Explicación sección por sección:

1. **`on: push: branches: [main]`**: Este es el "gatillo". El pipeline solo se dispara automáticamente cuando hacemos un `git push` a la rama `main`.
2. **`runs-on: self-hosted`**: Es la configuración más importante. Le dice a GitHub: *"No uses tus servidores, busca una computadora registrada con la etiqueta 'self-hosted' y ejecuta esto allí"*. Esa computadora es tu propia PC gracias al Runner en segundo plano.
3. **Checkout**: Descarga la última versión de tu código desde GitHub al entorno de ejecución (tu PC).
4. **Construcción de la Imagen**: Ejecuta `docker build` en tu PC usando el Dockerfile de la carpeta `./src/backend`.
5. **Inyección en Kind**: Dado que Kind usa sus propios nodos virtuales y no puede acceder al registro local de Docker de tu PC, usamos el comando `kind load` para "empujar" la imagen recién construida directamente al clúster, evitando el temido error `ErrImageNeverPull`.
6. **Despliegue en Kubernetes**: Aplica (o actualiza) los archivos YAML al clúster usando `kubectl apply`. Observa el `|| true` en la carpeta `01` para que no falle si el namespace ya existía.
7. **Verificación**: Un simple comando final para imprimir la lista de Pods en los registros (logs) de GitHub Actions.

---

## 2. Pipeline de Documentación (`docs.yml`)

Este flujo se encarga de convertir nuestros archivos Markdown (`.md`) en una página web hermosa y profesional usando MkDocs, y luego subirla a GitHub Pages.

```yaml
name: docs
on:
  push:
    branches:
      - main
permissions:
  contents: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Configure Git Credentials
        run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com
      - uses: actions/setup-python@v5
        with:
          python-version: 3.x
      - run: pip install mkdocs mkdocs-material
      - run: mkdocs gh-deploy --force
```

### Explicación sección por sección:

1. **`permissions: contents: write`**: Autoriza al bot de GitHub Actions a modificar el repositorio. Es necesario porque el flujo creará archivos compilados y hará un commit de ellos de forma automática.
2. **`runs-on: ubuntu-latest`**: A diferencia del anterior, este sí se ejecuta en la nube de GitHub, en un servidor Linux efímero gratuito.
3. **Configure Git Credentials**: Le damos una identidad al bot ("github-actions[bot]") para que GitHub sepa quién está haciendo el commit de la página generada.
4. **`setup-python@v5`**: Instala Python en el servidor de GitHub (necesario ya que MkDocs es una herramienta construida en Python).
5. **Instalación de herramientas**: Descarga e instala `mkdocs` y el tema visual `mkdocs-material` vía `pip`.
6. **`mkdocs gh-deploy --force`**: El comando mágico. MkDocs lee nuestros archivos Markdown, los convierte en una página web interactiva con HTML/CSS/JS, y automáticamente sube esos archivos a una rama oculta de nuestro repositorio llamada `gh-pages` para publicarlos en internet.
