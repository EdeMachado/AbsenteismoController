# Mapping Profile Versioning

## Entity

`ingestion_mapping_profiles`: id, client_id, name, version, structural_signature, mapping_json, sheet, header_row, active, created_at, created_by, replaces_version, status, observation.

## Rules

- Always tenant-scoped; never shared across clients
- Layout change ⇒ **new version row** (prior marked `superseded`, history kept)
- No destructive UPDATE of mapping JSON on prior versions
- Low-confidence mappings still require confirmation even with profile

## SQL

Upgrade: `backend/ingestion/sql/001_epic1_ingestion_up.sql`  
Downgrade: `001_epic1_ingestion_down.sql` (drops only `ingestion_*`)
