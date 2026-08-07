# Column Mapping Contract

## Canonical fields

See `CANONICAL_FIELDS` in `schemas.py`. **CPF is never obrigatório** (`restrito`).

## Resolution order

1. Client profile override  
2. Exact / alias (normalized: case, space, accents)  
3. Controlled lexical similarity (≥ 0.86; confirm if &lt; 0.92)  
4. Weak type hint (always needs confirmation)  
5. Unmapped  

## Output per column

`coluna_origem`, `campo_canonico`, `confianca`, `metodo`, `necessita_confirmacao`.

Low confidence ⇒ never auto-apply without confirmation.
