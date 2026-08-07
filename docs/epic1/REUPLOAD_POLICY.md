# Reupload Policy

## Classes

- `NOVO_ARQUIVO`
- `ARQUIVO_BRUTO_IDENTICO` — block auto-import
- `CONTEUDO_NORMALIZADO_IDENTICO` — block (includes rename)
- `MESMA_COMPETENCIA_CONTEUDO_DIFERENTE` — aggregate diff only
- `POSSIVEL_COMPLEMENTAR` — admin justification required
- `LAYOUT_ALTERADO` — confirm new profile version
- `INDETERMINADO`

## Diff

Aggregate counts only: new / missing / altered / totals. **Never** expose line contents in managerial reupload report.

Scope: tenant + competência + hashes + structural signature + line fingerprints.
