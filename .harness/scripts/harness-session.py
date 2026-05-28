#!/usr/bin/env python3
"""HarnessDB — Session Summary.

Genera un resumen inteligente del estado del proyecto para el inicio de sesión.
Combina datos de HarnessDB + CodeGraph para un overview completo.

Uso: python3 .harness/scripts/harness-session.py
"""
import sqlite3
import os
import sys
import json
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HARNESS_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(HARNESS_DIR)
DB_PATH = os.path.join(HARNESS_DIR, "harness.db")
CODEGRAPH_PATH = os.path.join(PROJECT_ROOT, ".codegraph", "codegraph.db")


def get_harness_conn():
    if not os.path.exists(DB_PATH):
        print("⚠️  HarnessDB no encontrada. Ejecutar: python3 .harness/scripts/harness-init.py")
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_codegraph_conn():
    if not os.path.exists(CODEGRAPH_PATH):
        return None
    conn = sqlite3.connect(CODEGRAPH_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def print_header():
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║            📊 HARNESS SESSION BRIEF                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()


def section_tasks(conn):
    """Resumen de tareas activas/pendientes."""
    try:
        tasks = conn.execute(
            "SELECT id, agent, description, current_step, status, started_at "
            "FROM active_tasks WHERE status IN ('in_progress', 'paused') ORDER BY updated_at DESC"
        ).fetchall()
        
        if not tasks:
            print("  ⏳ Tareas Activas: ninguna (todo al día)")
            return
            
        print(f"  ⏳ Tareas Activas: {len(tasks)} pendiente(s)")
        for t in tasks:
            status_icon = "▶️" if t['status'] == 'in_progress' else "⏸️"
            step_info = f" (Paso actual: {t['current_step']})" if t['current_step'] else ""
            print(f"     └─ {status_icon} [#{t['id']}] {t['description']}{step_info} — {t['agent']}")
    except sqlite3.OperationalError:
        pass  # Si la tabla no existe (antes de v2)

def section_codegraph():
    """Resumen del CodeGraph."""
    conn = get_codegraph_conn()
    if not conn:
        print("  ⚠️  CodeGraph no disponible")
        return

    files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    print(f"  📁 CodeGraph: {files} archivos indexados, {nodes} nodos, {edges} relaciones")
    conn.close()


def section_decisions(conn):
    """Resumen de decisiones."""
    total = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM decisions WHERE status='active'").fetchone()[0]

    if total == 0:
        print("  📋 Decisiones: ninguna registrada")
        return

    # Por dominio
    domains = conn.execute(
        "SELECT domain, COUNT(*) as cnt FROM decisions WHERE status='active' GROUP BY domain ORDER BY cnt DESC"
    ).fetchall()
    domain_str = ", ".join(f"{r['cnt']} en {r['domain']}" for r in domains)

    print(f"  📋 Decisiones: {active} activas de {total} total ({domain_str})")

    # Última decisión
    last = conn.execute(
        "SELECT timestamp, title, agent FROM decisions ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    if last:
        print(f"     └─ Última: \"{last['title']}\" ({last['agent']}, {last['timestamp']})")


def section_lessons(conn):
    """Resumen de lecciones aprendidas."""
    total = conn.execute("SELECT COUNT(*) FROM lessons_learned").fetchone()[0]

    if total == 0:
        print("  📚 Lecciones: ninguna registrada")
        return

    categories = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM lessons_learned GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    cat_str = ", ".join(f"{r['cnt']} {r['category']}" for r in categories)

    critical = conn.execute(
        "SELECT COUNT(*) FROM lessons_learned WHERE severity='critical'"
    ).fetchone()[0]

    severity_note = f" (🔴 {critical} críticas)" if critical > 0 else ""

    print(f"  📚 Lecciones: {total} total ({cat_str}){severity_note}")


def section_resources(conn):
    """Resumen del resource registry."""
    total = conn.execute("SELECT COUNT(*) FROM resource_registry").fetchone()[0]

    if total == 0:
        print("  🗂️  Recursos: ninguno registrado")
        return

    status_icons = {"healthy": "🟢", "degraded": "🟡", "error": "🔴", "unknown": "⚪"}
    statuses = conn.execute(
        "SELECT validation_status, COUNT(*) as cnt FROM resource_registry GROUP BY validation_status"
    ).fetchall()
    status_str = ", ".join(f"{status_icons.get(r['validation_status'], '⚪')}{r['cnt']} {r['validation_status']}" for r in statuses)

    print(f"  🗂️  Recursos: {total} registrados ({status_str})")

    # Recursos sin validar recientemente (más de 7 días o nunca)
    stale = conn.execute(
        """SELECT kind, name FROM resource_registry
           WHERE last_validated IS NULL
           OR last_validated < datetime('now', '-7 days')"""
    ).fetchall()
    if stale:
        stale_names = ", ".join(f"{r['kind']}/{r['name']}" for r in stale[:5])
        extra = f" (+{len(stale)-5} más)" if len(stale) > 5 else ""
        print(f"     └─ ⚠️  Pendientes de validación: {stale_names}{extra}")


def section_activity(conn):
    """Resumen de actividad reciente."""
    total = conn.execute("SELECT COUNT(*) FROM agent_activity_log").fetchone()[0]

    if total == 0:
        print("  📜 Actividad: ninguna registrada")
        return

    # Última actividad
    last = conn.execute(
        "SELECT timestamp, agent, action, summary FROM agent_activity_log ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()

    # Actividad últimas 24h
    recent = conn.execute(
        "SELECT COUNT(*) FROM agent_activity_log WHERE timestamp > datetime('now', '-1 day')"
    ).fetchone()[0]

    # Agentes activos últimas 24h
    agents = conn.execute(
        "SELECT DISTINCT agent FROM agent_activity_log WHERE timestamp > datetime('now', '-1 day')"
    ).fetchall()
    agent_str = ", ".join(r['agent'] for r in agents) if agents else "ninguno"

    print(f"  📜 Actividad: {total} total, {recent} en últimas 24h")
    if last:
        print(f"     └─ Última: [{last['agent']}] {last['action']}: {last['summary']} ({last['timestamp']})")
    if agents:
        print(f"     └─ Agentes activos (24h): {agent_str}")


def section_alerts(conn):
    """Alertas y recomendaciones."""
    alerts = []

    # Decisiones sin tags (difíciles de buscar)
    untagged = conn.execute(
        "SELECT COUNT(*) FROM decisions WHERE tags IS NULL AND status='active'"
    ).fetchone()[0]
    if untagged > 0:
        alerts.append(f"  ⚠️  {untagged} decisiones activas sin tags (difíciles de buscar)")

    # Recursos en error
    errors = conn.execute(
        "SELECT kind, name FROM resource_registry WHERE validation_status='error'"
    ).fetchall()
    for r in errors:
        alerts.append(f"  🔴 Recurso en ERROR: {r['kind']}/{r['name']}")

    # Lecciones críticas no resueltas
    unresolved = conn.execute(
        "SELECT title FROM lessons_learned WHERE severity='critical' AND resolution IS NULL"
    ).fetchall()
    for r in unresolved:
        alerts.append(f"  🔴 Lección crítica sin resolución: {r['title']}")

    if alerts:
        print()
        print("  ⚡ ALERTAS:")
        for a in alerts:
            print(f"  {a}")


def main():
    print_header()

    # CodeGraph summary
    section_codegraph()

    # HarnessDB sections
    conn = get_harness_conn()
    if conn:
        section_tasks(conn)
        section_decisions(conn)
        section_lessons(conn)
        section_resources(conn)
        section_activity(conn)
        section_alerts(conn)
        conn.close()
    else:
        print("  ⚠️  Ejecutar harness-init.py para habilitar memoria persistente")

    print()
    print("─" * 62)
    print()


if __name__ == "__main__":
    main()
