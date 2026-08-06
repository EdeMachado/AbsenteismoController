# Epic 1 — Database Change Plan

## Additive only

New tables: `ingestion_raw_files`, `ingestion_mapping_profiles`, `ingestion_executions`, `ingestion_line_errors`, `ingestion_canonical_rows`.

Scripts:

- Up: `backend/ingestion/sql/001_epic1_ingestion_up.sql`
- Down: `backend/ingestion/sql/001_epic1_ingestion_down.sql`

## Preconditions (future activation — not this PR)

1. Backup SQLite (`absenteismo.db`) verified restore  
2. Apply on staging copy first  
3. Smoke: table exists + legacy row counts unchanged  
4. Never run from app startup  
5. Never `DROP`/`ALTER` legacy tables  

## This PR

Scripts + `schema_sql.apply_epic1_schema` for **temp/test** only. Production not touched. Deploy/migration **out of scope**.
