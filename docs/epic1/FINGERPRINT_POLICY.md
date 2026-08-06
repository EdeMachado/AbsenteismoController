# Fingerprint Policy

## Raw hash

SHA-256 of original bytes.

## Structural signature

Hash of normalized column names + inferred types + sheet + header row.

## Normalized content hash

Stable ordering of canonical normalized values. Excludes filename/timestamps. CPF never plaintext — optional `cpf_hash` fragment only.

## Line fingerprint

Hash over allowed fields (matrícula, dates, dias, cid, setor, cc) + hashed identity — **no CPF plaintext stored in fingerprint string**.

## Idempotency key

`client_id | competência | content_hash | profile_version | pipeline_version` → SHA-256.
