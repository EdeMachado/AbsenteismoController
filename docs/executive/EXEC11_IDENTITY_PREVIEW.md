# EXEC-11 — BioMed Executive Identity Preview

**Status:** Draft · sem merge · sem deploy · sem produção  
**Branch:** `cursor/exec11-visual-identity-f8f5`

## O que é

Identidade visual definitiva BioMed (cover, closing, paleta, tipografia, espaçamento, ícones, fundos, signature, motion discreto).

**Não altera** Analytics, Meeting, Decision nem Evidence.

## Como abrir o preview

### Opção A — Rota isolada (recomendado)

Com o app local/staging:

```bash
# qualquer ambiente; rota não exige ENABLE_EXECUTIVE_UI nem login
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 18083
```

Abrir:

- http://127.0.0.1:18083/preview/executive  
- ou http://127.0.0.1:18083/staging/executive-preview  

Sem autenticação. Sem dados reais. Conteúdo 100% sintético.

### Opção B — HTML estático

Arquivo:

`frontend/preview/executive-identity.html`

Servir a pasta `frontend` (para `/static/...` resolver):

```bash
cd frontend && python3 -m http.server 8765
# abrir http://127.0.0.1:8765/preview/executive-identity.html
```

### Opção C — PDF executivo

`tests/artifacts/executive_identity/EXEC11_BioMed_Executive_Identity.pdf`

### Screenshots

`tests/artifacts/executive_identity/exec11_*.png`

## Controles

- Sem merge · sem deploy · sem produção  
- Sem migration  
- Parar após EXEC-11 — não iniciar EXEC-12
