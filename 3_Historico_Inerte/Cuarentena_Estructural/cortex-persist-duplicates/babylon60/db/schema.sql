PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    core_optimization_vector TEXT NOT NULL CHECK (
        core_optimization_vector IN ('ARTE_PURO', 'RECONOCIMIENTO_LIQUIDO', 'PROTECCION_DE_IDENTIDAD')
    ),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS thresholds (
    project_id INTEGER PRIMARY KEY,
    default_decision_threshold REAL NOT NULL DEFAULT 0.80 CHECK (default_decision_threshold BETWEEN 0.0 AND 1.0),
    distribution_floor REAL NOT NULL DEFAULT 0.25 CHECK (distribution_floor BETWEEN 0.0 AND 1.0),
    originality_floor REAL NOT NULL DEFAULT 0.35 CHECK (originality_floor BETWEEN 0.0 AND 1.0),
    anchor_lock_days INTEGER NOT NULL DEFAULT 30 CHECK (anchor_lock_days BETWEEN 1 AND 3650),
    colapse_interval_cycles INTEGER NOT NULL DEFAULT 12 CHECK (colapse_interval_cycles BETWEEN 1 AND 100000),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'PAUSED', 'CLOSED', 'ABORTED')),
    started_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    ended_at TEXT,
    notes TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('THINK', 'INPUT', 'OUTPUT', 'DECISION', 'ABORT', 'ANCHOR_LOCK', 'ANCHOR_RELEASE', 'METRIC')
    ),
    payload TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('AUDIO', 'VISUAL', 'TEXT', 'CODE', 'JSON', 'BINARY')),
    uri TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS metrics (
    session_id INTEGER PRIMARY KEY,
    think_to_exec_ms INTEGER NOT NULL DEFAULT 0 CHECK (think_to_exec_ms >= 0),
    originality_ratio REAL NOT NULL DEFAULT 0.0 CHECK (originality_ratio BETWEEN 0.0 AND 1.0),
    recombination_ratio REAL NOT NULL DEFAULT 0.0 CHECK (recombination_ratio BETWEEN 0.0 AND 1.0),
    default_decision_ratio REAL NOT NULL DEFAULT 0.0 CHECK (default_decision_ratio BETWEEN 0.0 AND 1.0),
    distribution_yield REAL NOT NULL DEFAULT 0.0 CHECK (distribution_yield BETWEEN 0.0 AND 1.0),
    aesthetic_hash TEXT NOT NULL DEFAULT '',
    rupture_count INTEGER NOT NULL DEFAULT 0 CHECK (rupture_count >= 0),
    last_updated TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS anchors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    path TEXT NOT NULL,
    locked_until TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, label)
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    decision_type TEXT NOT NULL CHECK (decision_type IN ('APPROVE', 'REJECT', 'ABORT', 'LOCK', 'RELEASE')),
    rationale TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_project_id ON sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_events_session_id_created_at ON events(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_session_id ON artifacts(session_id);
CREATE INDEX IF NOT EXISTS idx_anchors_project_id ON anchors(project_id);

CREATE TRIGGER IF NOT EXISTS trg_sessions_init_metrics
AFTER INSERT ON sessions
BEGIN
    INSERT INTO metrics(session_id) VALUES (NEW.id);
END;

CREATE TRIGGER IF NOT EXISTS trg_artifacts_require_hash
BEFORE INSERT ON artifacts
WHEN NEW.content_hash IS NULL OR LENGTH(TRIM(NEW.content_hash)) = 0
BEGIN
    SELECT RAISE(ABORT, 'content_hash requerido');
END;

CREATE TRIGGER IF NOT EXISTS trg_events_touch_session_start
AFTER INSERT ON events
WHEN NEW.event_type = 'THINK'
BEGIN
    UPDATE sessions
    SET started_at = COALESCE(started_at, NEW.created_at)
    WHERE id = NEW.session_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_events_close_on_abort
AFTER INSERT ON events
WHEN NEW.event_type = 'ABORT'
BEGIN
    UPDATE sessions
    SET status = 'ABORTED',
        ended_at = NEW.created_at
    WHERE id = NEW.session_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_decisions_mark_close
AFTER INSERT ON decisions
WHEN NEW.decision_type IN ('ABORT')
BEGIN
    UPDATE sessions
    SET status = 'ABORTED',
        ended_at = NEW.created_at
    WHERE id = NEW.session_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_anchors_require_path
BEFORE INSERT ON anchors
WHEN NEW.path IS NULL OR LENGTH(TRIM(NEW.path)) = 0
BEGIN
    SELECT RAISE(ABORT, 'path requerido');
END;
