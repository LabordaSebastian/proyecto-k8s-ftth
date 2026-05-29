#!/usr/bin/env python3
"""HarnessDB — Escritura de datos.

CLI para que los agentes registren información en la memoria del proyecto.

Uso:
  python3 .harness/scripts/harness-write.py decision --agent X --domain X --title X --context X --decision X [opts]
  python3 .harness/scripts/harness-write.py lesson --agent X --category X --title X --description X [opts]
  python3 .harness/scripts/harness-write.py resource --kind X --name X --manifest-path X [opts]
  python3 .harness/scripts/harness-write.py activity --agent X --action X --target X --summary X [opts]
  python3 .harness/scripts/harness-write.py snapshot --trigger X --description X [opts]
"""
import sqlite3
import argparse
import json
import os
import sys
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "harness.db")


def get_conn():
    if not os.path.exists(DB_PATH):
        print("❌ HarnessDB no encontrada. Ejecutar: python3 .harness/scripts/harness-init.py")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def to_json(value):
    """Convierte string comma-separated a JSON array, o retorna None."""
    if not value:
        return None
    if value.startswith("["):
        return value  # Already JSON
    return json.dumps([x.strip() for x in value.split(",")], ensure_ascii=False)


# ─── DECISION ────────────────────────────────────────────────────────

def write_decision(args):
    conn = get_conn()
    conn.execute(
        """INSERT INTO decisions
           (agent, domain, title, context, decision, alternatives, consequences, related_files, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            args.agent, args.domain, args.title, args.context, args.decision,
            to_json(args.alternatives), args.consequences,
            to_json(args.related_files), to_json(args.tags)
        )
    )
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"✅ Decisión registrada: #{row_id} — {args.title}")


# ─── LESSON ──────────────────────────────────────────────────────────

def write_lesson(args):
    conn = get_conn()
    conn.execute(
        """INSERT INTO lessons_learned
           (agent, category, title, description, root_cause, resolution, prevention,
            related_files, related_decisions, severity, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            args.agent, args.category, args.title, args.description,
            args.root_cause, args.resolution, args.prevention,
            to_json(args.related_files), to_json(args.related_decisions),
            args.severity or "info", to_json(args.tags)
        )
    )
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"✅ Lección registrada: #{row_id} — {args.title}")


def delete_lesson(args):
    conn = get_conn()
    cur = conn.execute("DELETE FROM lessons_learned WHERE id = ?", (args.lesson_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    if deleted:
        print(f"✅ Lección #{args.lesson_id} eliminada exitosamente.")
    else:
        print(f"⚠️ No se encontró la lección #{args.lesson_id}.")


# ─── RESOURCE ────────────────────────────────────────────────────────

def write_resource(args):
    conn = get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO resource_registry
           (kind, name, namespace, manifest_path, labels, dependencies,
            exposed_ports, validation_status, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            args.kind, args.name, args.namespace or "default",
            args.manifest_path, to_json(args.labels),
            to_json(args.dependencies), to_json(args.exposed_ports),
            args.validation_status or "unknown", args.notes
        )
    )
    conn.commit()
    conn.close()
    print(f"✅ Recurso registrado: {args.kind}/{args.name}")


# ─── ACTIVITY ────────────────────────────────────────────────────────

def write_activity(args):
    conn = get_conn()
    conn.execute(
        """INSERT INTO agent_activity_log
           (agent, action, target, summary, files_changed, validation_result, session_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            args.agent, args.action, args.target, args.summary,
            to_json(args.files_changed), args.validation_result, args.session_id
        )
    )
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"✅ Actividad registrada: #{row_id} — [{args.agent}] {args.action}: {args.summary}")


# ─── SNAPSHOT ────────────────────────────────────────────────────────

def write_snapshot(args):
    conn = get_conn()
    conn.execute(
        """INSERT INTO context_snapshots
           (trigger, description, cluster_state, manifest_versions, agent, tags)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            args.trigger, args.description, args.cluster_state,
            args.manifest_versions, args.agent, to_json(args.tags)
        )
    )
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"✅ Snapshot registrado: #{row_id} — [{args.trigger}] {args.description}")


# ─── UPDATE STATUS ───────────────────────────────────────────────────

def update_resource_status(args):
    """Actualiza el estado de validación de un recurso."""
    conn = get_conn()
    cur = conn.execute(
        """UPDATE resource_registry
           SET validation_status = ?, last_validated = datetime('now'), updated_at = datetime('now')
           WHERE kind = ? AND name = ? AND namespace = ?""",
        (args.validation_status, args.kind, args.name, args.namespace or "default")
    )
    conn.commit()
    if cur.rowcount == 0:
        print(f"⚠️  Recurso no encontrado: {args.kind}/{args.name} en {args.namespace or 'default'}")
    else:
        print(f"✅ Estado actualizado: {args.kind}/{args.name} → {args.validation_status}")
    conn.close()


# ─── SUPERSEDE DECISION ─────────────────────────────────────────────

def supersede_decision(args):
    """Marca una decisión como superseded por otra."""
    conn = get_conn()
    conn.execute(
        "UPDATE decisions SET status = 'superseded', superseded_by = ? WHERE id = ?",
        (args.new_id, args.old_id)
    )
    conn.commit()
    conn.close()
    print(f"✅ Decisión #{args.old_id} marcada como superseded por #{args.new_id}")


# ─── ACTIVE TASKS (MEMORIA DE CORTO PLAZO) ──────────────────────────

def write_task_start(args):
    """Inicia o retoma una tarea."""
    conn = get_conn()
    conn.execute(
        """INSERT INTO active_tasks
           (agent, description, status, current_step, session_id)
           VALUES (?, ?, 'in_progress', ?, ?)""",
        (args.agent, args.description, args.current_step, args.session_id)
    )
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"✅ Tarea iniciada/retomada: #{row_id} — [{args.agent}] {args.description}")

def write_task_update(args):
    """Actualiza el progreso de una tarea."""
    conn = get_conn()
    conn.execute(
        """UPDATE active_tasks
           SET current_step = ?, status = ?, updated_at = datetime('now')
           WHERE id = ?""",
        (args.current_step, args.status or 'in_progress', args.task_id)
    )
    conn.commit()
    conn.close()
    print(f"✅ Tarea #{args.task_id} actualizada: {args.current_step}")

def write_task_complete(args):
    """Marca una tarea como completada."""
    conn = get_conn()
    conn.execute(
        """UPDATE active_tasks
           SET status = 'completed', updated_at = datetime('now')
           WHERE id = ?""",
        (args.task_id,)
    )
    conn.commit()
    conn.close()
    print(f"✅ Tarea #{args.task_id} marcada como completada.")


# ─── MAIN ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="HarnessDB — Escritura de datos",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Tipo de registro")

    # Decision
    dec = subparsers.add_parser("decision", help="Registrar una decisión arquitectónica")
    dec.add_argument("--agent", required=True)
    dec.add_argument("--domain", required=True)
    dec.add_argument("--title", required=True)
    dec.add_argument("--context", required=True)
    dec.add_argument("--decision", required=True)
    dec.add_argument("--alternatives", help="Comma-separated o JSON array")
    dec.add_argument("--consequences")
    dec.add_argument("--related-files", help="Comma-separated paths")
    dec.add_argument("--tags", help="Comma-separated tags")

    # Lesson
    les = subparsers.add_parser("lesson", help="Registrar una lección aprendida")
    les.add_argument("--agent", required=True)
    les.add_argument("--category", required=True, choices=["error", "optimization", "pattern", "gotcha", "tip"])
    les.add_argument("--title", required=True)
    les.add_argument("--description", required=True)
    les.add_argument("--root-cause")
    les.add_argument("--resolution")
    les.add_argument("--prevention")
    les.add_argument("--related-files", help="Comma-separated paths")
    les.add_argument("--related-decisions", help="Comma-separated decision IDs")
    les.add_argument("--severity", choices=["critical", "warning", "info"], default="info")
    les.add_argument("--tags", help="Comma-separated tags")

    # Delete Lesson
    dl = subparsers.add_parser("delete-lesson", help="Eliminar una lección aprendida")
    dl.add_argument("--lesson-id", type=int, required=True)

    # Resource
    res = subparsers.add_parser("resource", help="Registrar un recurso K8s")
    res.add_argument("--kind", required=True)
    res.add_argument("--name", required=True)
    res.add_argument("--namespace", default="default")
    res.add_argument("--manifest-path", required=True)
    res.add_argument("--labels", help="Comma-separated key=value")
    res.add_argument("--dependencies", help="Comma-separated resource names")
    res.add_argument("--exposed-ports", help="Comma-separated ports")
    res.add_argument("--validation-status", default="unknown")
    res.add_argument("--notes")

    # Activity
    act = subparsers.add_parser("activity", help="Registrar actividad de agente")
    act.add_argument("--agent", required=True)
    act.add_argument("--action", required=True, choices=["create", "modify", "validate", "diagnose", "document", "delete"])
    act.add_argument("--target", required=True)
    act.add_argument("--summary", required=True)
    act.add_argument("--files-changed", help="Comma-separated paths")
    act.add_argument("--validation-result", choices=["pass", "fail", "skipped"])
    act.add_argument("--session-id")

    # Snapshot
    snap = subparsers.add_parser("snapshot", help="Registrar snapshot de contexto")
    snap.add_argument("--trigger", required=True, choices=["post-deploy", "post-validation", "milestone", "manual"])
    snap.add_argument("--description", required=True)
    snap.add_argument("--cluster-state", help="JSON con estado del clúster")
    snap.add_argument("--manifest-versions", help="JSON con versiones de manifiestos")
    snap.add_argument("--agent")
    snap.add_argument("--tags", help="Comma-separated tags")

    # Update status
    upd = subparsers.add_parser("update-status", help="Actualizar estado de validación de un recurso")
    upd.add_argument("--kind", required=True)
    upd.add_argument("--name", required=True)
    upd.add_argument("--namespace", default="default")
    upd.add_argument("--validation-status", required=True, choices=["healthy", "degraded", "error", "unknown"])

    # Supersede
    sup = subparsers.add_parser("supersede", help="Marcar decisión como reemplazada")
    sup.add_argument("--old-id", type=int, required=True)
    sup.add_argument("--new-id", type=int, required=True)

    # Active Tasks
    ts = subparsers.add_parser("task-start", help="Iniciar/retomar tarea (memoria corto plazo)")
    ts.add_argument("--agent", required=True)
    ts.add_argument("--description", required=True)
    ts.add_argument("--current-step")
    ts.add_argument("--session-id")

    tu = subparsers.add_parser("task-update", help="Actualizar tarea activa")
    tu.add_argument("--task-id", type=int, required=True)
    tu.add_argument("--current-step", required=True)
    tu.add_argument("--status", choices=["in_progress", "paused", "completed"])

    tc = subparsers.add_parser("task-complete", help="Completar tarea activa")
    tc.add_argument("--task-id", type=int, required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "decision": write_decision,
        "lesson": write_lesson,
        "delete-lesson": delete_lesson,
        "resource": write_resource,
        "activity": write_activity,
        "snapshot": write_snapshot,
        "update-status": update_resource_status,
        "supersede": supersede_decision,
        "task-start": write_task_start,
        "task-update": write_task_update,
        "task-complete": write_task_complete,
    }

    commands[args.command](args)
    
    # Auto-update STATUS.md
    report_script = os.path.join(SCRIPT_DIR, "harness-report.py")
    if os.path.exists(report_script):
        os.system(f"python3 {report_script} > /dev/null 2>&1")


if __name__ == "__main__":
    main()
