# Epic 1 — Architecture

## Goal

Intelligent data ingestion pipeline as an **experimental** parallel path. Legacy upload remains untouched.

```
RAW bytes → metadata/hash → safe read → sheet/header → column map →
client profile → preview (no write) → IQB advisory → fingerprints →
reupload class → confirm → idempotent transactional import → canonical layer
```

## Package

`backend/ingestion/` — separated responsibilities (raw, reader, header, mapping, profiles, normalization, fingerprint, reupload, preview, import, API).

## Feature flag

`ENABLE_INTELLIGENT_INGESTION` default `false`.

When off: no API routes, no experimental page, no startup migration, legacy behavior unchanged.

## Persistence

Additive SQLite tables only (`ingestion_*`). Applied via explicit SQL scripts on **temp/test** DBs — never on production startup, never against `/var/www/absenteismo`.

Import writes to `ingestion_canonical_rows`, not legacy `atestados`.

## PR #4 readiness

`tenant_adapter.py` defines `TenantContext` / `TenantGuard`. API refuses unauthenticated requests. When PR #4 merges, wire `PR4_TENANT_GUARD_FACTORY` — do not duplicate auth.

## Checkpoints

| ID | Scope |
|----|--------|
| E1-C1 | RAW + reader + hash |
| E1-C2 | Mapping + profiles |
| E1-C3 | Preview + IQB adapter |
| E1-C4 | Fingerprints + reupload |
| E1-C5 | Confirm + import + idempotency |
| E1-C6 | Flag-gated API + experimental UI |
