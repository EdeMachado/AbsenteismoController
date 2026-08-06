# Spreadsheet Reader Contract

## Formats

| Format | Support |
|--------|---------|
| `.xlsx` | Yes (openpyxl, `data_only=False`, no macro execution) |
| `.csv` | Yes — delimiter `,` `;` tab; encoding utf-8 / cp1252 fallback with warning |
| `.xls` | **Not supported** — clear `UnsupportedFormatError` (no insecure xlrd) |

## Limits

MAX_SHEETS, MAX_PREVIEW_ROWS, MAX_COLUMNS, MAX_CELL_CHARS, MAX_CSV_LINES_SCAN.

## Safety

- Formula-like cells (`=`, `+`, `-`, `@` prefix) rejected
- Empty files rejected
- Ambiguous delimiter → warning (`delimiter_ambiguous_*` / near-tie)

## Header/sheet detection

Deterministic scoring: recognized tokens, fill, uniqueness, following density, breadth. Ambiguity ⇒ `necessita_confirmacao`.
