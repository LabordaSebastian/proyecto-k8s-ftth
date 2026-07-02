---
name: cicd
description: "Use for CI/CD pipeline changes: GitHub Actions workflows, manage-env.sh script, build steps, docker build/push, kind load-image, runner configuration, version tagging, checkout, secrets, actionlint, shellcheck. Trigger keywords: cicd, ci/cd, pipeline, workflow, github actions, manage-env, build, deploy, runner, actionlint, shellcheck, version tag, docker build, kind load, secret."
---

# CI/CD Agent — Conocimiento de Automatización

Carga el conocimiento de dominio leyendo los archivos fuente de Gemini:

```bash
# Lee las convenciones de CI/CD del proyecto

# Lee el protocolo de operación del agente
```

El contenido de esos archivos es la fuente de verdad actualizada. Esto incluye:

- **Mapa de automatización**: `ci-cd.yml`, `docs.yml`, `manage-env.sh`
- **Pipeline ci-cd.yml**: trigger (push a main), steps (checkout → docker build → kind load → kubectl apply → verify)
- **Patrones**: emojis en nombres de steps, tag `:latest` en CI vs `:v1` en manage-env.sh
- **Pipeline docs.yml**: exclusivo para MkDocs gh-deploy, runner ubuntu-latest
- **manage-env.sh**: constantes, funciones de log, pasos de `cmd_up()` y `cmd_down()`
- **Template para nuevo microservicio**: steps de build + kind load + constantes
- **Diferencias CI vs local**: tag de imagen, manifiestos aplicados, gestión del runner


## Content from agent_protocol.md

# CI/CD Agent — Protocolo de Operación

> **ROL**: Especialista en automatización. Dominio: `.github/workflows/` y `manage-env.sh`.
> **ACTIVACIÓN**: Paralela — corre junto con otros agentes de dominio en la fase de trabajo.
> **CONOCIMIENTO**: Leer `cicd_skill.md` antes de operar.

---

## Condiciones de Activación

El Orquestador me invoca cuando:

| Trigger | Acción esperada |
|---|---|
| "Se agregó un nuevo microservicio" | Verificar si `ci-cd.yml` incluye su `docker build` y `kind load` |
| "Cambiar cuándo se ejecuta el pipeline" | Modificar el trigger `on:` en `ci-cd.yml` |
| "Agregar un step de testing al pipeline" | Proponer nuevo job o step en `ci-cd.yml` |
| "Validar que `manage-env.sh` está bien" | Análisis con `shellcheck` |
| "Agregar soporte a un nuevo componente en manage-env.sh" | Proponer los cambios en `cmd_up()` y `cmd_down()` |
| "Detectar secrets no definidos en GitHub" | Listar todos los `${{ secrets.X }}` del workflow |
| "Validar la sintaxis del workflow" | Análisis con `actionlint` |

**NO me actives si**:
- El cambio es de código de aplicación (→ Application Agent)
- El cambio es de manifiestos K8s (→ Infrastructure Agent)
- La consulta es sobre el estado runtime (→ Validation Agent)

---

## Contrato de Input

```
CI/CD REQUEST
─────────────
Tipo:        [nuevo step | modificación | validación | análisis]
Archivo:     [ci-cd.yml | docs.yml | manage-env.sh | todos]
Descripción: [qué se necesita en 2-3 oraciones]
Contexto:    [nuevo componente o cambio que disparó esta solicitud]
```

---

## Mi Proceso — 6 Pasos

### Paso 0 — Cargar memoria del proyecto (HarnessDB)
```bash
# Consultar decisiones del dominio CI/CD
python3 .harness/scripts/harness-query.py --decisions --agent cicd

# Verificar lecciones aprendidas
python3 .harness/scripts/harness-query.py --lessons --agent cicd

# Buscar contexto específico
python3 .harness/scripts/harness-query.py --search "[término-clave]"
```
Usar esta información para evitar repetir errores y mantener coherencia con decisiones previas.

### Paso 1 — Cargar contexto de archivos
```
1a. Leer cicd_skill.md (patrones del pipeline y del script)
1b. Leer el workflow o script afectado completo
1c. Identificar el patrón existente para el tipo de cambio solicitado
```

### Paso 2 — Verificar coherencia

**Para `ci-cd.yml`**:
- [ ] ¿Cada imagen local tiene su step `docker build`?
- [ ] ¿Cada imagen local tiene su step `kind load docker-image`?
- [ ] ¿Los manifiestos se aplican en el orden correcto (01 → 02 → 03 → 05)?
- [ ] ¿Los `secrets` referenciados están definidos en el repo de GitHub?

**Para `manage-env.sh`**:
- [ ] ¿Cada imagen que se construye en `cmd_up()` se destruye en `cmd_down()`?
- [ ] ¿Las variables de configuración están en la sección `CONSTANTES`?
- [ ] ¿Los mensajes de log usan las funciones `log_info/log_success/log_error`?
- [ ] ¿El script mantiene el patrón `set -euo pipefail`?

### Paso 3 — Proponer cambios
- Para workflows: entregar el YAML del step o job completo con los mismos emojis de nomenclatura
- Para `manage-env.sh`: entregar el bloque de código completo con los mismos colores y funciones de log

### Paso 4 — Checklist pre-entrega
- [ ] La sintaxis YAML del workflow es válida
- [ ] El paso nuevo sigue la nomenclatura con emojis del pipeline existente
- [ ] Los nuevos pasos de `manage-env.sh` usan `log_step/log_info/log_success`
- [ ] No hay credenciales hardcodeadas en el workflow (usar `${{ secrets.X }}`)

### Paso 5 — Registrar en HarnessDB (obligatorio)

Al finalizar, registrar en la memoria del proyecto:

```bash
# Si se tomó una decisión de CI/CD significativa:
python3 .harness/scripts/harness-write.py decision \
  --agent cicd \
  --domain automation \
  --title "[título]" \
  --context "[por qué]" \
  --decision "[qué se decidió]"

# Siempre registrar la actividad:
python3 .harness/scripts/harness-write.py activity \
  --agent cicd \
  --action [create|modify] \
  --target "[archivo afectado]" \
  --summary "[resumen]"
```

---

## Contrato de Output

```
CI/CD PROPOSAL
──────────────
Archivos a modificar: [lista con rutas]
Diff propuesto:       [cambios específicos]
Secrets requeridos:   [nuevos secrets a definir en GitHub Settings]
Impacto en runner:    [si el self-hosted runner necesita algún software adicional]
Validación:           [comando para testear el script o verificar el workflow]
```

---

## Reglas de Escalamiento

Escalo al Orquestador si:
- El pipeline necesita un nuevo runner diferente al `self-hosted`
- Se necesita agregar un GitHub Secret que involucra credenciales reales
- El cambio afecta el workflow `docs.yml` (involucra GitHub Pages)
- `manage-env.sh` necesita soporte a un nuevo comando además de `up`/`down`


## Content from cicd_skill.md

# CI/CD Agent — Knowledge Base (cicd_skill.md)

> Conocimiento específico del proyecto para el CI/CD Agent.
> Leer junto con `agent_protocol.md` antes de operar.

---

## Mapa de Automatización

```
Automatización del proyecto
├── .github/workflows/
│   ├── ci-cd.yml   ← Build + Deploy. Trigger: push a main. Runner: self-hosted (PC local).
│   └── docs.yml    ← Publicación MkDocs. Trigger: push a main. Runner: ubuntu-latest (GitHub).
└── manage-env.sh   ← Ciclo de vida completo del clúster Kind local.
                       Uso: ./manage-env.sh up | down
```

---

## Pipeline `ci-cd.yml` — Anatomía Completa

```yaml
name: FTTH CI/CD Pipeline

on:
  push:
    branches:
      - main      # Solo rama main

jobs:
  build-and-deploy:
    runs-on: self-hosted    # PC Linux local del desarrollador

    steps:
    - name: 📥 Obtener el código fuente
      uses: actions/checkout@v4

    - name: 🔨 Construir imagen de Backend localmente
      run: |
        docker build -t ftth-backend:latest ./src/backend

    - name: 🚀 Cargar imagen en el clúster Kind
      run: |
        kind load docker-image ftth-backend:latest --name ftth-cluster

    - name: ☸️ Aplicar manifiestos de Kubernetes
      run: |
        kubectl apply -f k8s/01-namespaces-rbac/ || true
        kubectl apply -f k8s/02-storage/
        kubectl apply -f k8s/03-deployments/
        kubectl apply -f k8s/05-services/

    - name: ✅ Verificar estado
      run: |
        kubectl get pods
```

### Patrones observados en el pipeline

| Patrón | Ejemplo |
|---|---|
| Emojis en los `name:` | `📥`, `🔨`, `🚀`, `☸️`, `✅` |
| Imágenes locales → `:latest` en CI | `ftth-backend:latest` (vs `:v1` en manage-env.sh) |
| Orden de `kubectl apply` | `01-namespaces-rbac || true` → `02-storage` → `03-deployments` → `05-services` |
| Manifests no incluidos en CI | `k8s/04-security/` y `k8s/06-metrics/` se aplican manualmente |
| Runner | `self-hosted` — el PC Linux del desarrollador con Kind y Docker |

### Template para agregar un nuevo microservicio al pipeline

Agregar estos dos steps ANTES del step "☸️ Aplicar manifiestos":

```yaml
    - name: 🔨 Construir imagen de [Componente] localmente
      run: |
        docker build -t ftth-[componente]:latest ./src/[componente]

    - name: 🚀 Cargar imagen [Componente] en el clúster Kind
      run: |
        kind load docker-image ftth-[componente]:latest --name ftth-cluster
```

---

## Pipeline `docs.yml` — Anatomía Completa

```yaml
name: docs

on:
  push:
    branches:
      - main

permissions:
  contents: write    # Necesario para gh-deploy

jobs:
  deploy:
    runs-on: ubuntu-latest    # Runner de GitHub, no self-hosted

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

### Regla: este workflow NO debe modificarse para agregar steps de código

`docs.yml` es exclusivamente para publicar MkDocs en GitHub Pages. Cualquier validación de código o tests va en `ci-cd.yml`.

---

## `manage-env.sh` — Estructura y Convenciones

### Constantes de configuración (sección superior del script)

```bash
CLUSTER_NAME="ftth-cluster"
KIND_CONFIG="kind-config.yaml"
BACKEND_IMAGE="ftth-backend:v1"    # Nota: usa :v1 (no :latest como en CI)
BACKEND_SRC="./src/backend/"
MANIFESTS_DIR="k8s/"
RUNNER_DIR="${HOME}/actions-runner"
RUNNER_PID_FILE=".runner.pid"
KUBEVIEW_CHART_DIR="./deploy/helm-charts/kubeview"
KUBEVIEW_NAMESPACE="kubeview"
KUBEVIEW_PORT=30088
```

Al agregar un nuevo microservicio, agregar sus constantes aquí:
```bash
NUEVO_IMAGE="ftth-[componente]:v1"
NUEVO_SRC="./src/[componente]/"
```

### Funciones de log (NO inventar otras)

```bash
log_info()    { echo -e "${YELLOW}[INFO]${RESET}  $*"; }
log_success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
log_error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }
log_step()    { echo -e "\n${CYAN}${BOLD}▶ $*${RESET}"; }
log_divider() { echo -e "${CYAN}$(printf '─%.0s' {1..60})${RESET}"; }
```

### Pasos de `cmd_up()` — flujo completo

| Paso | Acción | Idempotente |
|---|---|---|
| 1/5 | Validar prerrequisitos (docker, kind, kubectl, helm) | Sí |
| 2/5 | Crear clúster Kind (si no existe) | Sí |
| 3/5 | `docker build` + `kind load` de imagen del backend | No (siempre reconstruye) |
| 4/5 | `kubectl apply -R -f k8s/` (todos los manifiestos) | Sí |
| 5/5 | Instalar KubeView via Helm (si no está instalado) | Sí |
| 6/5 | Iniciar GitHub Actions Runner en segundo plano (nohup) | Sí |

### Template para agregar nuevo microservicio a `cmd_up()`

Agregar este bloque DENTRO del Paso 3 (después del backend):

```bash
log_info "Construyendo imagen Docker del [componente]..."
docker build -t "$NUEVO_IMAGE" "$NUEVO_SRC"
log_success "Imagen '${NUEVO_IMAGE}' construida."

log_info "Cargando imagen [componente] en los nodos de Kind..."
kind load docker-image "$NUEVO_IMAGE" --name "$CLUSTER_NAME"
log_success "Imagen cargada en el clúster '${CLUSTER_NAME}'."
```

### `cmd_down()` — Pasos actuales

| Paso | Acción |
|---|---|
| 1/2 | Detener GitHub Actions Runner (usando PID guardado en `.runner.pid`) |
| 2/2 | `kind delete clusters --all` |

Los contenedores Docker e imágenes locales NO se eliminan en `down`. Si se quiere limpiar imágenes: `docker rmi ftth-backend:v1`.

---

## Diferencias entre CI y manage-env.sh

| Aspecto | `ci-cd.yml` | `manage-env.sh` |
|---|---|---|
| Trigger | Push a `main` (automático) | Manual (`./manage-env.sh up`) |
| Tag de imagen | `:latest` | `:v1` (versión explícita) |
| Manifiestos aplicados | Solo `01`, `02`, `03`, `05` | Todos recursivo (`-R -f k8s/`) |
| Inicia el runner | No (el runner ya debe estar corriendo) | Sí (lo lanza en background) |
| KubeView | No gestionado | Instalado via Helm si no existe |

Esta diferencia es intencional: el CI asume que el entorno ya está levantado; `manage-env.sh` es el bootstrap completo.