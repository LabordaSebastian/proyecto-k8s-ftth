#!/usr/bin/env python3
"""HarnessDB — Inicialización de la base de datos.

Crea .harness/harness.db si no existe y aplica el schema.
Si ya existe, verifica la versión y aplica migraciones pendientes.

Uso: python3 .harness/scripts/harness-init.py
"""
import sqlite3
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HARNESS_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(HARNESS_DIR, "harness.db")
SCHEMA_PATH = os.path.join(HARNESS_DIR, "schema.sql")
SEED_PATH = os.path.join(HARNESS_DIR, "seed.sql")

CURRENT_SCHEMA_VERSION = 2


def get_db_version(conn):
    """Retorna la versión actual del schema, o 0 si no existe."""
    try:
        cur = conn.execute("SELECT MAX(version) FROM schema_info")
        row = cur.fetchone()
        return row[0] if row and row[0] else 0
    except sqlite3.OperationalError:
        return 0


def init_db():
    """Inicializa o actualiza la base de datos."""
    db_exists = os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    version = get_db_version(conn)

    if version >= CURRENT_SCHEMA_VERSION:
        print(f"✅ HarnessDB ya está en v{version} (actual: v{CURRENT_SCHEMA_VERSION})")
        print(f"   📍 {DB_PATH}")
        report_stats(conn)
        conn.close()
        return

    if version == 0:
        # Aplicar schema inicial
        if not os.path.exists(SCHEMA_PATH):
            print(f"❌ No se encontró {SCHEMA_PATH}")
            sys.exit(1)

        print("🔧 Creando HarnessDB v1...")
        with open(SCHEMA_PATH, "r") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        print("   ✅ Schema aplicado (5 tablas + FTS + triggers)")

        # Aplicar seed si existe
        if os.path.exists(SEED_PATH):
            print("🌱 Aplicando datos iniciales...")
            with open(SEED_PATH, "r") as f:
                seed_sql = f.read()
            conn.executescript(seed_sql)
            print("   ✅ Seed aplicado")
        else:
            print("   ⚠️  No se encontró seed.sql (se puede ejecutar después)")

    if version < 2:
        apply_migration_v2(conn)

    print(f"\n✅ HarnessDB inicializada correctamente")
    print(f"   📍 {DB_PATH}")
    report_stats(conn)
    conn.close()


def report_stats(conn):
    """Muestra estadísticas rápidas de la DB."""
    tables = {
        "active_tasks": "Tareas Activas",
        "decisions": "Decisiones",
        "context_snapshots": "Snapshots",
        "lessons_learned": "Lecciones",
        "resource_registry": "Recursos",
        "agent_activity_log": "Actividades",
    }
    print("\n   📊 Estado actual:")
    for table, label in tables.items():
        try:
            cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"      {label}: {count} registros")
        except sqlite3.OperationalError:
            print(f"      {label}: ⚠️ tabla no encontrada")


def apply_migration_v2(conn):
    print("🔧 Aplicando migración a v2 (active_tasks)...")
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS active_tasks (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                agent           TEXT NOT NULL,
                description     TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'in_progress',
                current_step    TEXT,
                started_at      TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
                session_id      TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_active_tasks_status ON active_tasks(status)")
        conn.execute("INSERT INTO schema_info (version, description) VALUES (2, 'Added active_tasks')")
        conn.commit()
        print("   ✅ Migración a v2 completada.")
    except Exception as e:
        print(f"   ❌ Error en migración v2: {e}")


if __name__ == "__main__":
    init_db()
