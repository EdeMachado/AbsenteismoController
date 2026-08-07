-- Epic 1 additive schema (SQLite) — NEVER run on production startup.
-- Upgrade: apply this file to a backed-up copy / staging / temp DB only.
-- Downgrade: see 001_epic1_ingestion_down.sql (DROP only epic1 tables; never touch legacy).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ingestion_raw_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    competencia TEXT NOT NULL,
    original_name TEXT NOT NULL,
    safe_storage_name TEXT NOT NULL,
    extension TEXT NOT NULL,
    mime_type TEXT,
    size_bytes INTEGER NOT NULL,
    sha256_raw TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'received',
    pipeline_version TEXT NOT NULL,
    uploaded_by TEXT,
    received_at TEXT NOT NULL,
    UNIQUE(client_id, sha256_raw)
);

CREATE TABLE IF NOT EXISTS ingestion_mapping_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    version INTEGER NOT NULL,
    structural_signature TEXT NOT NULL,
    mapping_json TEXT NOT NULL,
    sheet_name TEXT,
    header_row INTEGER,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    created_by TEXT,
    replaces_version INTEGER,
    status TEXT NOT NULL DEFAULT 'active',
    observation TEXT,
    UNIQUE(client_id, name, version)
);

CREATE TABLE IF NOT EXISTS ingestion_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_uuid TEXT NOT NULL UNIQUE,
    raw_file_id INTEGER,
    client_id INTEGER NOT NULL,
    competencia TEXT NOT NULL,
    profile_id INTEGER,
    profile_version INTEGER,
    mode TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    status TEXT NOT NULL,
    total_rows INTEGER DEFAULT 0,
    valid_rows INTEGER DEFAULT 0,
    alert_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,
    inserted_rows INTEGER DEFAULT 0,
    ignored_rows INTEGER DEFAULT 0,
    structural_signature TEXT,
    content_hash_normalized TEXT,
    idempotency_key TEXT,
    safe_message TEXT,
    correlation_id TEXT,
    confirmation_token_hash TEXT,
    preview_payload_json TEXT,
    FOREIGN KEY(raw_file_id) REFERENCES ingestion_raw_files(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ingestion_idempotency
    ON ingestion_executions(client_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL AND status IN ('succeeded', 'idempotent_hit');

CREATE TABLE IF NOT EXISTS ingestion_line_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    field TEXT,
    error_code TEXT NOT NULL,
    safe_message TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'error',
    FOREIGN KEY(execution_id) REFERENCES ingestion_executions(id)
);

CREATE TABLE IF NOT EXISTS ingestion_canonical_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    competencia TEXT NOT NULL,
    line_fingerprint TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(execution_id) REFERENCES ingestion_executions(id),
    UNIQUE(client_id, competencia, line_fingerprint, execution_id)
);

CREATE INDEX IF NOT EXISTS idx_ingestion_raw_client_comp
    ON ingestion_raw_files(client_id, competencia);

CREATE INDEX IF NOT EXISTS idx_ingestion_exec_client
    ON ingestion_executions(client_id, competencia);
