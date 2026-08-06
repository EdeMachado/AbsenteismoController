-- Epic 1 downgrade — drops ONLY epic1 additive tables.
-- NEVER drop or alter legacy tables (atestados, users, clients, uploads, etc.).
-- Run only on temp/staging DBs after backup verification.

DROP TABLE IF EXISTS ingestion_line_errors;
DROP TABLE IF EXISTS ingestion_canonical_rows;
DROP TABLE IF EXISTS ingestion_executions;
DROP TABLE IF EXISTS ingestion_mapping_profiles;
DROP TABLE IF EXISTS ingestion_raw_files;
