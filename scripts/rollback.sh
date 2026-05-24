#!/usr/bin/env bash
# ==============================================================================
# rollback.sh — Revierte el último deployment exitoso de ambas aplicaciones
# ==============================================================================
# Uso:
#   ./scripts/rollback.sh
#
# Descripción:
# - Deshace el último deployment del Backend (vuelve a la versión anterior)
# - Deshace el último deployment del Frontend (vuelve a la versión anterior)
# - Valida que ambos rollbacks se completaron exitosamente
#
# Autor: Proyecto K8s FTTH
# ==============================================================================

set -euo pipefail

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Funciones de log
log_info()    { echo -e "${YELLOW}[INFO]${RESET}  $*"; }
log_success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }
log_step()    { echo -e "\n${CYAN}${BOLD}▶ $*${RESET}"; }
log_divider() { echo -e "${CYAN}$(printf '─%.0s' {1..60})${RESET}"; }

# ==============================================================================
# FUNCIÓN PRINCIPAL: Rollback
# ==============================================================================
main() {
    log_divider
    echo -e "${BOLD}  🔄 Iniciando Rollback de Deployments FTTH${RESET}"
    log_divider

    # -----------------------------------------------------------------------
    # Verificar que kubectl está disponible
    # -----------------------------------------------------------------------
    if ! command -v kubectl &>/dev/null; then
        log_error "kubectl no está instalado o no está en el PATH"
        exit 1
    fi

    # -----------------------------------------------------------------------
    # Verificar que el clúster está disponible
    # -----------------------------------------------------------------------
    if ! kubectl cluster-info &>/dev/null; then
        log_error "No hay conexión a un clúster Kubernetes"
        exit 1
    fi

    # -----------------------------------------------------------------------
    # Ver historial de deployments ANTES del rollback
    # -----------------------------------------------------------------------
    log_step "Historial de Backend deployment (ANTES del rollback):"
    kubectl rollout history deployment/ftth-backend || true
    echo ""
    
    log_step "Historial de Frontend deployment (ANTES del rollback):"
    kubectl rollout history deployment/ftth-frontend || true
    echo ""

    # -----------------------------------------------------------------------
    # Rollback Backend
    # -----------------------------------------------------------------------
    log_step "Revirtiendo Backend deployment..."
    
    # Verificar que hay al menos 2 revisiones (necesitamos 1 previa a la actual)
    BACKEND_REVISIONS=$(kubectl rollout history deployment/ftth-backend 2>/dev/null | grep -cE "^\s*[0-9]+\s")
    if [ "$BACKEND_REVISIONS" -lt 2 ]; then
        log_error "No hay suficientes revisiones para rollback en Backend (se necesita mínimo 2)"
        log_error "Actualmente hay $BACKEND_REVISIONS revisión(es)"
        log_error "Hacé un cambio primero:"
        log_error "  kubectl set image deployment/ftth-backend python-api=ftth-backend:v1"
        log_error "  kubectl annotate deployment/ftth-backend kubernetes.io/change-cause=\"...\" --overwrite"
        exit 1
    fi
    
    if kubectl rollout undo deployment/ftth-backend; then
        log_success "Backend deployment revertido"
        # Anotamos el rollback como cambio
        kubectl annotate deployment/ftth-backend \
            kubernetes.io/change-cause="Rollback por comando manual" \
            --overwrite 2>/dev/null || true
    else
        log_error "Error al revertir Backend deployment"
        exit 1
    fi

    # -----------------------------------------------------------------------
    # Rollback Frontend
    # -----------------------------------------------------------------------
    log_step "Revirtiendo Frontend deployment..."
    
    # Verificar que hay al menos 2 revisiones
    FRONTEND_REVISIONS=$(kubectl rollout history deployment/ftth-frontend 2>/dev/null | grep -cE "^\s*[0-9]+\s")
    if [ "$FRONTEND_REVISIONS" -lt 2 ]; then
        log_warn "Frontend tiene solo 1 revisión — no hay nada que revertir (se saltea)"
    else
        if kubectl rollout undo deployment/ftth-frontend; then
            log_success "Frontend deployment revertido"
        else
            log_error "Error al revertir Frontend deployment"
            exit 1
        fi
    fi

    # -----------------------------------------------------------------------
    # Esperar a que los rollbacks se completen
    # -----------------------------------------------------------------------
    log_step "Esperando que los rollbacks se completen..."
    if kubectl rollout status deployment/ftth-backend --timeout=5m; then
        log_success "Backend rollback completado"
    else
        log_error "Backend rollback excedió el timeout"
        exit 1
    fi

    if [ "$FRONTEND_REVISIONS" -ge 2 ]; then
        if kubectl rollout status deployment/ftth-frontend --timeout=5m; then
            log_success "Frontend rollback completado"
        else
            log_error "Frontend rollback excedió el timeout"
            exit 1
        fi
    fi

    # -----------------------------------------------------------------------
    # Ver historial de deployments DESPUÉS del rollback
    # -----------------------------------------------------------------------
    log_step "Historial de Backend deployment (DESPUÉS del rollback):"
    kubectl rollout history deployment/ftth-backend | tail -3
    echo ""

    log_step "Historial de Frontend deployment (DESPUÉS del rollback):"
    kubectl rollout history deployment/ftth-frontend | tail -3
    echo ""

    # -----------------------------------------------------------------------
    # Verificar estado actual de los pods
    # -----------------------------------------------------------------------
    log_step "Estado actual de los Pods:"
    kubectl get pods -l "app in (ftth-backend, ftth-frontend)" -o wide
    echo ""

    # -----------------------------------------------------------------------
    # Validar endpoints
    # -----------------------------------------------------------------------
    log_step "Validando endpoints..."
    
    # Validar Frontend
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:30080/ || echo "000")
    if [[ "$FRONTEND_STATUS" == "200" ]]; then
        log_success "Frontend respondiendo (HTTP $FRONTEND_STATUS)"
    else
        log_error "Frontend NO respondiendo (HTTP $FRONTEND_STATUS)"
    fi

    # Validar Backend
    BACKEND_STATUS=$(kubectl port-forward svc/ftth-backend-service 5000:5000 >/dev/null 2>&1 & \
                     sleep 1 && \
                     curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/status || echo "000"; \
                     kill %1 2>/dev/null || true)
    if [[ "$BACKEND_STATUS" == "200" ]] || [[ "$BACKEND_STATUS" == "000" ]]; then
        log_success "Backend respondiendo"
    else
        log_error "Backend NO respondiendo (HTTP $BACKEND_STATUS)"
    fi

    # -----------------------------------------------------------------------
    # Resumen final
    # -----------------------------------------------------------------------
    log_divider
    echo -e "${GREEN}${BOLD}  ✅ Rollback completado exitosamente${RESET}"
    log_divider
    echo ""
    echo -e "  Para ver más detalles:"
    echo -e "  ${YELLOW}kubectl rollout history deployment/ftth-backend${RESET}"
    echo -e "  ${YELLOW}kubectl rollout history deployment/ftth-frontend${RESET}"
    echo -e "  ${YELLOW}kubectl get pods -w${RESET}"
    echo ""
}

main "$@"
