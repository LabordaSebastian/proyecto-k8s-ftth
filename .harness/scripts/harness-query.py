#!/usr/bin/env python3
"""HarnessDB — Consultas de lectura.

CLI para que los agentes consulten la memoria del proyecto.

Uso:
  python3 .harness/scripts/harness-query.py --decisions [--domain X] [--agent X] [--status active]
  python3 .harness/scripts/harness-query.py --lessons [--category X] [--severity X]
  python3 .harness/scripts/harness-query.py --resources [--kind X] [--status X]
  python3 .harness/scripts/harness-query.py --activity [--agent X] [--last N]
  python3 .harness/scripts/harness-query.py --snapshots [--last N]
  python3 .harness/scripts/harness-query.py --search "término de búsqueda"
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
    conn.row_factory = sqlite3.Row
    return conn


def fmt_json(val):
    """Formatea un campo JSON para display."""
    if not val:
        return "—"
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return ", ".join(str(x) for x in parsed)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return str(val)


def print_separator():
    print("─" * 70)


# ─── DECISIONS ───────────────────────────────────────────────────────

def query_decisions(args):
    conn = get_conn()
    query = "SELECT * FROM decisions WHERE 1=1"
    params = []

    if args.domain:
        query += " AND domain = ?"
        params.append(args.domain)
    if args.agent:
        query += " AND agent = ?"
        params.append(args.agent)
    if args.status:
        query += " AND status = ?"
        params.append(args.status)
    else:
        query += " AND status = 'active'"

    query += " ORDER BY timestamp DESC"
    if args.last:
        query += f" LIMIT {args.last}"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("📭 No se encontraron decisiones con esos filtros.")
        return

    print(f"\n📋 DECISIONES ({len(rows)} encontradas)")
    print_separator()
    for r in rows:
        print(f"  🆔 #{r['id']}  [{r['status'].upper()}]  {r['timestamp']}")
        print(f"  📌 {r['title']}")
        print(f"  🏷️  Agente: {r['agent']}  |  Dominio: {r['domain']}")
        print(f"  📝 Contexto: {r['context']}")
        print(f"  ✅ Decisión: {r['decision']}")
        if r['alternatives']:
            print(f"  🔄 Alternativas: {fmt_json(r['alternatives'])}")
        if r['consequences']:
            print(f"  ⚠️  Consecuencias: {r['consequences']}")
        if r['related_files']:
            print(f"  📁 Archivos: {fmt_json(r['related_files'])}")
        if r['tags']:
            print(f"  🏷️  Tags: {fmt_json(r['tags'])}")
        print_separator()


# ─── LESSONS ─────────────────────────────────────────────────────────

def query_lessons(args):
    conn = get_conn()
    query = "SELECT * FROM lessons_learned WHERE 1=1"
    params = []

    if args.category:
        query += " AND category = ?"
        params.append(args.category)
    if args.severity:
        query += " AND severity = ?"
        params.append(args.severity)
    if args.agent:
        query += " AND agent = ?"
        params.append(args.agent)

    query += " ORDER BY timestamp DESC"
    if args.last:
        query += f" LIMIT {args.last}"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("📭 No se encontraron lecciones con esos filtros.")
        return

    severity_icons = {"critical": "🔴", "warning": "🟡", "info": "🔵"}

    print(f"\n📚 LECCIONES APRENDIDAS ({len(rows)} encontradas)")
    print_separator()
    for r in rows:
        icon = severity_icons.get(r['severity'], "⚪")
        print(f"  🆔 #{r['id']}  {icon} [{r['severity'].upper()}]  {r['timestamp']}")
        print(f"  📌 {r['title']}")
        print(f"  🏷️  Agente: {r['agent']}  |  Categoría: {r['category']}")
        print(f"  📝 {r['description']}")
        if r['root_cause']:
            print(f"  🔍 Causa raíz: {r['root_cause']}")
        if r['resolution']:
            print(f"  ✅ Resolución: {r['resolution']}")
        if r['prevention']:
            print(f"  🛡️  Prevención: {r['prevention']}")
        if r['tags']:
            print(f"  🏷️  Tags: {fmt_json(r['tags'])}")
        print_separator()


# ─── RESOURCES ───────────────────────────────────────────────────────

def query_resources(args):
    conn = get_conn()
    query = "SELECT * FROM resource_registry WHERE 1=1"
    params = []

    if args.kind:
        query += " AND kind = ?"
        params.append(args.kind)
    if args.status:
        query += " AND validation_status = ?"
        params.append(args.status)

    query += " ORDER BY kind, name"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("📭 No se encontraron recursos con esos filtros.")
        return

    status_icons = {"healthy": "🟢", "degraded": "🟡", "error": "🔴", "unknown": "⚪"}

    print(f"\n🗂️  RESOURCE REGISTRY ({len(rows)} recursos)")
    print_separator()
    print(f"  {'Estado':<8} {'Tipo':<15} {'Nombre':<30} {'Namespace':<12} {'Manifiesto'}")
    print_separator()
    for r in rows:
        icon = status_icons.get(r['validation_status'], "⚪")
        print(f"  {icon:<8} {r['kind']:<15} {r['name']:<30} {r['namespace']:<12} {r['manifest_path']}")
    print_separator()

    # Summary by status
    for status in ["healthy", "degraded", "error", "unknown"]:
        count = sum(1 for r in rows if r['validation_status'] == status)
        if count > 0:
            icon = status_icons[status]
            print(f"  {icon} {status}: {count}")


# ─── ACTIVITY ────────────────────────────────────────────────────────

def query_activity(args):
    conn = get_conn()
    query = "SELECT * FROM agent_activity_log WHERE 1=1"
    params = []

    if args.agent:
        query += " AND agent = ?"
        params.append(args.agent)
    if args.action:
        query += " AND action = ?"
        params.append(args.action)

    query += " ORDER BY timestamp DESC"
    limit = args.last if args.last else 20
    query += f" LIMIT {limit}"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("📭 No se encontró actividad con esos filtros.")
        return

    action_icons = {
        "create": "🆕", "modify": "✏️", "validate": "✅",
        "diagnose": "🔍", "document": "📝", "delete": "🗑️"
    }

    print(f"\n📜 ACTIVIDAD DE AGENTES (últimas {len(rows)} entradas)")
    print_separator()
    for r in rows:
        icon = action_icons.get(r['action'], "▪️")
        result = ""
        if r['validation_result']:
            result = f" → [{r['validation_result']}]"
        print(f"  {r['timestamp']}  {icon} [{r['agent']}] {r['action']}: {r['summary']}{result}")
        if r['files_changed']:
            print(f"                    📁 {fmt_json(r['files_changed'])}")
    print_separator()


# ─── SNAPSHOTS ───────────────────────────────────────────────────────

def query_snapshots(args):
    conn = get_conn()
    query = "SELECT * FROM context_snapshots ORDER BY timestamp DESC"
    limit = args.last if args.last else 5
    query += f" LIMIT {limit}"

    rows = conn.execute(query).fetchall()
    conn.close()

    if not rows:
        print("📭 No se encontraron snapshots.")
        return

    print(f"\n📸 CONTEXT SNAPSHOTS (últimos {len(rows)})")
    print_separator()
    for r in rows:
        print(f"  🆔 #{r['id']}  {r['timestamp']}  [{r['trigger']}]")
        print(f"  📝 {r['description']}")
        if r['agent']:
            print(f"  🤖 Agente: {r['agent']}")
        print_separator()


# ─── SEARCH (FTS) ────────────────────────────────────────────────────

def search_all(args):
    conn = get_conn()
    term = args.search

    print(f"\n🔍 Búsqueda: \"{term}\"")
    print_separator()

    # Search decisions
    rows = conn.execute(
        "SELECT d.* FROM decisions d JOIN decisions_fts f ON d.id = f.rowid "
        "WHERE decisions_fts MATCH ? ORDER BY rank",
        (term,)
    ).fetchall()
    if rows:
        print(f"\n  📋 Decisiones ({len(rows)} resultados):")
        for r in rows:
            print(f"     #{r['id']} [{r['domain']}] {r['title']}")

    # Search lessons
    rows = conn.execute(
        "SELECT l.* FROM lessons_learned l JOIN lessons_fts f ON l.id = f.rowid "
        "WHERE lessons_fts MATCH ? ORDER BY rank",
        (term,)
    ).fetchall()
    if rows:
        print(f"\n  📚 Lecciones ({len(rows)} resultados):")
        for r in rows:
            print(f"     #{r['id']} [{r['category']}] {r['title']}")

    # Search resources by name
    rows = conn.execute(
        "SELECT * FROM resource_registry WHERE name LIKE ? OR kind LIKE ?",
        (f"%{term}%", f"%{term}%")
    ).fetchall()
    if rows:
        print(f"\n  🗂️  Recursos ({len(rows)} resultados):")
        for r in rows:
            print(f"     {r['kind']}/{r['name']} → {r['manifest_path']}")

    print_separator()
    conn.close()


# ─── MAIN ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="HarnessDB — Consultas de lectura",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Ejemplos:
              %(prog)s --decisions --domain networking
              %(prog)s --lessons --category error --severity critical
              %(prog)s --resources --kind Deployment
              %(prog)s --activity --agent infrastructure --last 10
              %(prog)s --search "redis affinity"
        """)
    )

    # Query type
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--decisions", action="store_true", help="Consultar decisiones")
    group.add_argument("--lessons", action="store_true", help="Consultar lecciones aprendidas")
    group.add_argument("--resources", action="store_true", help="Consultar resource registry")
    group.add_argument("--activity", action="store_true", help="Consultar log de actividad")
    group.add_argument("--snapshots", action="store_true", help="Consultar snapshots de contexto")
    group.add_argument("--search", type=str, metavar="TERM", help="Búsqueda full-text en toda la DB")

    # Filters
    parser.add_argument("--domain", type=str, help="Filtrar por dominio")
    parser.add_argument("--agent", type=str, help="Filtrar por agente")
    parser.add_argument("--status", type=str, help="Filtrar por estado")
    parser.add_argument("--category", type=str, help="Filtrar lecciones por categoría")
    parser.add_argument("--severity", type=str, help="Filtrar lecciones por severidad")
    parser.add_argument("--kind", type=str, help="Filtrar recursos por tipo K8s")
    parser.add_argument("--action", type=str, help="Filtrar actividad por acción")
    parser.add_argument("--last", type=int, help="Limitar a los últimos N resultados")

    args = parser.parse_args()

    if args.decisions:
        query_decisions(args)
    elif args.lessons:
        query_lessons(args)
    elif args.resources:
        query_resources(args)
    elif args.activity:
        query_activity(args)
    elif args.snapshots:
        query_snapshots(args)
    elif args.search:
        search_all(args)


if __name__ == "__main__":
    main()
