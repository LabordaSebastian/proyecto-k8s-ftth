-- ============================================================
-- HarnessDB Schema v1.0
-- Memoria persistente compartida para agentes Harness Engineering
-- ============================================================

-- Metadatos del schema
CREATE TABLE IF NOT EXISTS schema_info (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT
);

INSERT INTO schema_info (version, description) VALUES (1, 'Initial schema — 5 core tables');
INSERT INTO schema_info (version, description) VALUES (2, 'Added active_tasks for short-term memory');

-- ============================================================
-- Tabla 0: active_tasks — Memoria de corto plazo (tareas en progreso)
-- ============================================================
CREATE TABLE IF NOT EXISTS active_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT NOT NULL,
    description     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'in_progress', -- in_progress, paused, completed
    current_step    TEXT,
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    session_id      TEXT
);

CREATE INDEX IF NOT EXISTS idx_active_tasks_status ON active_tasks(status);


-- ============================================================
-- Tabla 1: decisions — Registro de Decisiones Arquitectónicas
-- ============================================================
CREATE TABLE IF NOT EXISTS decisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    agent           TEXT NOT NULL,
    domain          TEXT NOT NULL,
    title           TEXT NOT NULL,
    context         TEXT NOT NULL,
    decision        TEXT NOT NULL,
    alternatives    TEXT,           -- JSON array
    consequences    TEXT,
    related_files   TEXT,           -- JSON array
    status          TEXT NOT NULL DEFAULT 'active',
    superseded_by   INTEGER,
    tags            TEXT,           -- JSON array
    FOREIGN KEY (superseded_by) REFERENCES decisions(id)
);

CREATE INDEX IF NOT EXISTS idx_decisions_domain ON decisions(domain);
CREATE INDEX IF NOT EXISTS idx_decisions_agent ON decisions(agent);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);

-- ============================================================
-- Tabla 2: context_snapshots — Snapshots de Estado del Proyecto
-- ============================================================
CREATE TABLE IF NOT EXISTS context_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    trigger         TEXT NOT NULL,
    description     TEXT NOT NULL,
    cluster_state   TEXT,           -- JSON
    manifest_versions TEXT,         -- JSON
    agent           TEXT,
    tags            TEXT            -- JSON array
);

CREATE INDEX IF NOT EXISTS idx_snapshots_trigger ON context_snapshots(trigger);

-- ============================================================
-- Tabla 3: lessons_learned — Lecciones Aprendidas
-- ============================================================
CREATE TABLE IF NOT EXISTS lessons_learned (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    agent           TEXT NOT NULL,
    category        TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    root_cause      TEXT,
    resolution      TEXT,
    prevention      TEXT,
    related_files   TEXT,           -- JSON array
    related_decisions TEXT,         -- JSON array of decision IDs
    severity        TEXT DEFAULT 'info',
    tags            TEXT            -- JSON array
);

CREATE INDEX IF NOT EXISTS idx_lessons_category ON lessons_learned(category);
CREATE INDEX IF NOT EXISTS idx_lessons_severity ON lessons_learned(severity);

-- ============================================================
-- Tabla 4: resource_registry — Registro Vivo de Recursos K8s
-- ============================================================
CREATE TABLE IF NOT EXISTS resource_registry (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    kind                TEXT NOT NULL,
    name                TEXT NOT NULL,
    namespace           TEXT DEFAULT 'default',
    manifest_path       TEXT NOT NULL,
    labels              TEXT,           -- JSON
    dependencies        TEXT,           -- JSON array
    exposed_ports       TEXT,           -- JSON array
    last_validated      TEXT,
    validation_status   TEXT DEFAULT 'unknown',
    notes               TEXT,
    updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(kind, name, namespace)
);

CREATE INDEX IF NOT EXISTS idx_registry_kind ON resource_registry(kind);
CREATE INDEX IF NOT EXISTS idx_registry_status ON resource_registry(validation_status);

-- ============================================================
-- Tabla 5: agent_activity_log — Log de Actividad de Agentes
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_activity_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT NOT NULL DEFAULT (datetime('now')),
    agent               TEXT NOT NULL,
    action              TEXT NOT NULL,
    target              TEXT NOT NULL,
    summary             TEXT NOT NULL,
    input_hash          TEXT,
    files_changed       TEXT,           -- JSON array
    validation_result   TEXT,
    session_id          TEXT
);

CREATE INDEX IF NOT EXISTS idx_activity_agent ON agent_activity_log(agent);
CREATE INDEX IF NOT EXISTS idx_activity_action ON agent_activity_log(action);
CREATE INDEX IF NOT EXISTS idx_activity_session ON agent_activity_log(session_id);

-- ============================================================
-- FTS (Full-Text Search) para búsquedas semánticas
-- ============================================================
CREATE VIRTUAL TABLE IF NOT EXISTS decisions_fts USING fts5(
    title,
    context,
    decision,
    consequences,
    content='decisions',
    content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS lessons_fts USING fts5(
    title,
    description,
    root_cause,
    resolution,
    content='lessons_learned',
    content_rowid='id'
);

-- Triggers para mantener FTS sincronizado con las tablas base
CREATE TRIGGER IF NOT EXISTS decisions_ai AFTER INSERT ON decisions BEGIN
    INSERT INTO decisions_fts(rowid, title, context, decision, consequences)
    VALUES (new.id, new.title, new.context, new.decision, new.consequences);
END;

CREATE TRIGGER IF NOT EXISTS decisions_ad AFTER DELETE ON decisions BEGIN
    INSERT INTO decisions_fts(decisions_fts, rowid, title, context, decision, consequences)
    VALUES ('delete', old.id, old.title, old.context, old.decision, old.consequences);
END;

CREATE TRIGGER IF NOT EXISTS decisions_au AFTER UPDATE ON decisions BEGIN
    INSERT INTO decisions_fts(decisions_fts, rowid, title, context, decision, consequences)
    VALUES ('delete', old.id, old.title, old.context, old.decision, old.consequences);
    INSERT INTO decisions_fts(rowid, title, context, decision, consequences)
    VALUES (new.id, new.title, new.context, new.decision, new.consequences);
END;

CREATE TRIGGER IF NOT EXISTS lessons_ai AFTER INSERT ON lessons_learned BEGIN
    INSERT INTO lessons_fts(rowid, title, description, root_cause, resolution)
    VALUES (new.id, new.title, new.description, new.root_cause, new.resolution);
END;

CREATE TRIGGER IF NOT EXISTS lessons_ad AFTER DELETE ON lessons_learned BEGIN
    INSERT INTO lessons_fts(lessons_fts, rowid, title, description, root_cause, resolution)
    VALUES ('delete', old.id, old.title, old.description, old.root_cause, old.resolution);
END;

CREATE TRIGGER IF NOT EXISTS lessons_au AFTER UPDATE ON lessons_learned BEGIN
    INSERT INTO lessons_fts(lessons_fts, rowid, title, description, root_cause, resolution)
    VALUES ('delete', old.id, old.title, old.description, old.root_cause, old.resolution);
    INSERT INTO lessons_fts(rowid, title, description, root_cause, resolution)
    VALUES (new.id, new.title, new.description, new.root_cause, new.resolution);
END;
