#!/usr/bin/env bash
# ==============================================================================
# manage-env.sh — Gestor del entorno local de desarrollo FTTH
# ==============================================================================
# Uso:
#   ./manage-env.sh up    →  Levanta el clúster completo + GitHub Runner
#   ./manage-env.sh down  →  Destruye el clúster + detiene el GitHub Runner
#
# Autor: Proyecto K8s FTTH
# ==============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# CONSTANTES Y CONFIGURACIÓN
# ------------------------------------------------------------------------------
CLUSTER_NAME="ftth-cluster"
KIND_CONFIG="kind-config.yaml"
# Image versioning strategy: Use git tags or increment version
# Format: ftth-backend:vX where X is version number
BACKEND_VERSION="${BACKEND_VERSION:-v1}"  # Can be overridden: BACKEND_VERSION=v2 ./manage-env.sh up
BACKEND_IMAGE="ftth-backend:${BACKEND_VERSION}"
BACKEND_SRC="./src/backend/"
MANIFESTS_DIR="k8s/"
RUNNER_DIR="${HOME}/actions-runner"
RUNNER_PID_FILE=".runner.pid"
KUBEVIEW_CHART_DIR="./deploy/helm-charts/kubeview"
KUBEVIEW_NAMESPACE="kubeview"
KUBEVIEW_PORT=30088

# ------------------------------------------------------------------------------
# COLORES PARA MENSAJES
# ------------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ------------------------------------------------------------------------------
# FUNCIONES DE LOG
# ------------------------------------------------------------------------------
log_info()    { echo -e "${YELLOW}[INFO]${RESET}  $*"; }
log_success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
log_error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }
log_step()    { echo -e "\n${CYAN}${BOLD}▶ $*${RESET}"; }
log_divider() { echo -e "${CYAN}$(printf '─%.0s' {1..60})${RESET}"; }

# ------------------------------------------------------------------------------
# FUNCIÓN: Validaciones previas al arranque
# Verifica que todas las herramientas necesarias estén disponibles y operativas.
# ------------------------------------------------------------------------------
validate_prerequisites() {
    log_step "Validando prerequisitos..."
    local errors=0

    # Verificar comandos requeridos
    for cmd in docker kind kubectl helm; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "Comando '$cmd' no encontrado. Por favor instalalo antes de continuar."
            (( errors++ )) || true
        fi
    done

    # Verificar que Docker esté corriendo (no solo instalado)
    if ! docker info &>/dev/null; then
        log_error "Docker no está corriendo. Inicialo antes de ejecutar este script."
        (( errors++ )) || true
    fi

    # Verificar que el archivo de config de Kind exista
    if [[ ! -f "$KIND_CONFIG" ]]; then
        log_error "No se encontró el archivo '$KIND_CONFIG'. Ejecutá el script desde la raíz del proyecto."
        (( errors++ )) || true
    fi

    # Verificar que el directorio del runner exista
    if [[ ! -d "$RUNNER_DIR" ]]; then
        log_error "No se encontró el directorio del GitHub Actions Runner en '$RUNNER_DIR'."
        (( errors++ )) || true
    fi

    if [[ $errors -gt 0 ]]; then
        log_error "Se encontraron $errors error(es). Abortando."
        exit 1
    fi

    log_success "Todos los prerequisitos están OK."
}

# ------------------------------------------------------------------------------
# FUNCIÓN: Levantar el entorno completo
# ------------------------------------------------------------------------------
cmd_up() {
    log_divider
    echo -e "${BOLD}  🚀 Levantando entorno FTTH — Kubernetes + GitHub Runner${RESET}"
    log_divider

    validate_prerequisites

    # ------------------------------------------------------------------
    # PASO 1: Crear el clúster Kind si no existe
    # ------------------------------------------------------------------
    log_step "Paso 1/5 — Verificando clúster Kind..."
    if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        log_info "El clúster '${CLUSTER_NAME}' ya existe. Omitiendo creación."
    else
        log_info "Clúster no encontrado. Creando '${CLUSTER_NAME}'..."
        kind create cluster --config "$KIND_CONFIG"
        log_success "Clúster '${CLUSTER_NAME}' creado exitosamente."
    fi

    # ------------------------------------------------------------------
    # PASO 2: Build y carga de imágenes locales en Kind
    # IMPORTANTE: Kind corre sus nodos como contenedores Docker y NO tiene
    # acceso al registry local del host. Sin este paso, los pods quedarán
    # en estado ErrImageNeverPull indefinidamente.
    # ------------------------------------------------------------------
    log_step "Paso 2/5 — Construyendo imagen Docker del backend..."
    docker build -t "$BACKEND_IMAGE" "$BACKEND_SRC"
    log_success "Imagen '${BACKEND_IMAGE}' construida."

    log_info "Cargando imagen en los nodos de Kind..."
    kind load docker-image "$BACKEND_IMAGE" --name "$CLUSTER_NAME"
    log_success "Imagen cargada en el clúster '${CLUSTER_NAME}'."

    # ------------------------------------------------------------------
    # PASO 3: Instalar Vertical Pod Autoscaler (VPA) via Helm
    # Es necesario que los CRDs de VPA existan ANTES de aplicar k8s/07-autoscaling
    # ------------------------------------------------------------------
    log_step "Paso 3/6 — Verificando Vertical Pod Autoscaler (VPA)..."
    if helm status vpa --namespace vpa &>/dev/null; then
        log_info "VPA ya está instalado. Omitiendo."
    else
        log_info "Instalando VPA via Helm (fairwinds-stable/vpa)..."
        helm repo add fairwinds-stable https://charts.fairwinds.com/stable &>/dev/null
        helm repo update fairwinds-stable &>/dev/null
        helm install vpa fairwinds-stable/vpa --namespace vpa --create-namespace &>/dev/null
        log_success "VPA instalado correctamente."
    fi

    # ------------------------------------------------------------------
    # PASO 4: Aplicar manifiestos de Kubernetes
    # ------------------------------------------------------------------
    log_step "Paso 4/6 — Aplicando manifiestos de Kubernetes..."
    kubectl apply -R -f "$MANIFESTS_DIR"
    log_success "Manifiestos aplicados correctamente."

    # ------------------------------------------------------------------
    # PASO 5: Instalar KubeView si no está instalado
    # ------------------------------------------------------------------
    log_step "Paso 5/6 — Verificando KubeView..."
    if helm status kubeview --namespace "$KUBEVIEW_NAMESPACE" &>/dev/null; then
        log_info "KubeView ya está instalado. Omitiendo."
    elif [[ -d "$KUBEVIEW_CHART_DIR" ]]; then
        log_info "Instalando KubeView via Helm..."
        helm install kubeview "$KUBEVIEW_CHART_DIR" \
            --namespace "$KUBEVIEW_NAMESPACE" \
            --create-namespace \
            --set loadBalancer.enabled=false \
            --set nodePort.enabled=true \
            --set nodePort.port="$KUBEVIEW_PORT"
        log_success "KubeView instalado en el puerto ${KUBEVIEW_PORT}."
    else
        log_error "Chart de KubeView no encontrado en '${KUBEVIEW_CHART_DIR}'."
        log_error "El directorio deploy/helm-charts/kubeview debería existir en el repo."
        log_error "Si fue eliminado, restauralo con: git checkout deploy/helm-charts/"
        log_info "Continuando sin KubeView..."
    fi

    # ------------------------------------------------------------------
    # PASO 6: Iniciar GitHub Actions Runner en segundo plano
    # El runner no está configurado como servicio de systemd, por lo que
    # se lanza manualmente con nohup y se guarda su PID para poder
    # detenerlo limpiamente con el comando 'down'.
    # ------------------------------------------------------------------
    log_step "Paso 6/6 — Iniciando GitHub Actions Runner..."
    if [[ -f "$RUNNER_PID_FILE" ]] && kill -0 "$(cat "$RUNNER_PID_FILE")" 2>/dev/null; then
        log_info "El Runner ya está corriendo (PID: $(cat "$RUNNER_PID_FILE")). Omitiendo."
    else
        pushd "$RUNNER_DIR" > /dev/null
        nohup ./run.sh > runner.log 2>&1 &
        RUNNER_PID=$!
        popd > /dev/null
        echo "$RUNNER_PID" > "$RUNNER_PID_FILE"
        log_success "GitHub Actions Runner iniciado en segundo plano (PID: ${RUNNER_PID})."
        log_info "Logs del runner: ${RUNNER_DIR}/runner.log"
    fi

    # ------------------------------------------------------------------
    # Resumen final
    # ------------------------------------------------------------------
    log_divider
    echo -e "${GREEN}${BOLD}  ✅ Entorno FTTH levantado correctamente${RESET}"
    log_divider
    echo -e "  ${BOLD}URLs de acceso:${RESET}"
    echo -e "  🌐 Frontend FTTH Dashboard  →  ${CYAN}http://localhost:30080${RESET}"
    echo -e "  📊 KubeView (visualización) →  ${CYAN}http://localhost:30088${RESET}"
    echo ""
    echo -e "  Para detener todo:  ${YELLOW}./manage-env.sh down${RESET}"
    log_divider
    echo ""
}

# ------------------------------------------------------------------------------
# FUNCIÓN: Destruir el entorno completo
# ------------------------------------------------------------------------------
cmd_down() {
    log_divider
    echo -e "${BOLD}  🛑 Deteniendo entorno FTTH${RESET}"
    log_divider

    # ------------------------------------------------------------------
    # PASO 1: Detener el GitHub Actions Runner
    # Leemos el PID guardado durante el 'up' y lo terminamos limpiamente.
    # ------------------------------------------------------------------
    log_step "Paso 1/2 — Deteniendo GitHub Actions Runner..."
    if [[ -f "$RUNNER_PID_FILE" ]]; then
        RUNNER_PID=$(cat "$RUNNER_PID_FILE")
        if kill -0 "$RUNNER_PID" 2>/dev/null; then
            kill "$RUNNER_PID"
            log_success "Runner detenido (PID: ${RUNNER_PID})."
        else
            log_info "El proceso con PID ${RUNNER_PID} ya no estaba corriendo."
        fi
        rm -f "$RUNNER_PID_FILE"
        log_info "Archivo PID eliminado."
    else
        log_info "No se encontró el archivo '${RUNNER_PID_FILE}'. El runner puede no haber sido iniciado con este script."
    fi

    # ------------------------------------------------------------------
    # PASO 2: Destruir todos los clústeres Kind
    # ------------------------------------------------------------------
    log_step "Paso 2/2 — Destruyendo clúster Kind..."
    if kind get clusters 2>/dev/null | grep -q .; then
        kind delete clusters --all
        log_success "Todos los clústeres Kind han sido eliminados."
    else
        log_info "No hay clústeres Kind activos para eliminar."
    fi

    # ------------------------------------------------------------------
    # Resumen final
    # ------------------------------------------------------------------
    log_divider
    echo -e "${GREEN}${BOLD}  ✅ Entorno FTTH detenido correctamente${RESET}"
    log_divider
    echo ""
    echo -e "  Para volver a levantar todo:  ${YELLOW}./manage-env.sh up${RESET}"
    log_divider
    echo ""
}

# ------------------------------------------------------------------------------
# PUNTO DE ENTRADA PRINCIPAL — Parseo de argumentos
# ------------------------------------------------------------------------------
main() {
    if [[ $# -ne 1 ]]; then
        echo -e "${RED}Uso: $0 [up|down]${RESET}"
        echo ""
        echo "  up    Levanta el clúster Kind, carga imágenes, aplica manifiestos e inicia el runner."
        echo "  down  Detiene el runner y destruye el clúster Kind."
        exit 1
    fi

    case "$1" in
        up)   cmd_up ;;
        down) cmd_down ;;
        *)
            log_error "Argumento inválido: '$1'. Usá 'up' o 'down'."
            exit 1
            ;;
    esac
}

main "$@"
