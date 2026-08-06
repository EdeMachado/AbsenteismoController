# Preview Contract

## Guarantees

- No `commit`/`flush` into legacy business tables
- Optional write only to epic1 preview execution metadata
- Returns counts, mapping, IQB advisory, reupload class, recommended decision
- Sample rows **masked** (no full CPF/matricula/nome)

## Must not return

Full CPF, full matrícula, full names in managerial payloads, clinical free text, raw line dumps, internal filesystem paths.

## Confirmation

`confirmation_token` issued once; hashed at rest; required for confirm + import; single-use after import consume.
