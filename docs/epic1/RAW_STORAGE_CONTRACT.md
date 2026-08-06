# RAW Storage Contract

## Inputs

- File bytes (unmodified)
- Original filename
- `client_id`, `competencia`, optional uploader

## Outputs (`RawFileMetadata`)

original_name (sanitized), extension, MIME hint, size, SHA-256 raw, received_at UTC, client, competência, uploaded_by, safe_storage_name, status, pipeline_version, storage_key (internal only).

## Rules

- Hash over original bytes
- Never overwrite existing storage key
- Sanitize names; block path traversal on storage keys
- Size limit (`MAX_FILE_BYTES`)
- Allow `.xlsx`, `.csv`; reject `.xls`/macros/archives with clear errors
- No public web-root storage; `MemoryStorage` / `LocalTempStorage` for tests
- Public API must not return `storage_key` or full hash (partial only)
