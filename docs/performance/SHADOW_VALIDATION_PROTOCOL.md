# Protocolo de Validação Shadow — Epic 2A-B

## Objetivo

Validar o Performance Engine contra métricas canônicas + IQB em SQLite **readonly**, sem telas, sem endpoints e sem produção.

## Regras absolutas

- Não acessar VPS nem `/var/www/absenteismo/database/absenteismo.db`.
- Não insert/update/delete/migration/seed sobre a base analisada.
- Abrir apenas com `mode=ro` + `PRAGMA query_only=ON`.
- Path explícito obrigatório (`--db-path`).
- Recusar paths de produção / `absenteismo.db`.
- Validar `PRAGMA integrity_check` e schema (`clients`, `uploads`, `atestados`).
- Saída apenas agregada; guard anti-PII.
- Informar SHA-256 do arquivo, períodos, versão do motor e limitações.

## CLI

```bash
python scripts/shadow_performance_engine.py \
  --db-path /caminho/explicito/copia.sqlite \
  --client-id 2 \
  --baseline-inicio 2025-05 --baseline-fim 2025-07 \
  --atual-inicio 2026-05 --atual-fim 2026-07 \
  --productivity-json opcional.json \
  --conditionants-json opcional.json \
  --custo-programa 10000 \
  --custo-hora 50
```

## Produtividade BioMed

Ainda **não** integrada ao banco legado.

Permitido: ausência | fixture sintética | JSON agregado explícito.

Ausência → dimensão de cobertura não avaliada; pesos redistribuídos; limitação explícita.

## Condicionantes

Somente JSON agregado explícito (ação, decisão, status, prazo, barreira, risco residual). Sem leitura clínica. Sem novas tabelas.

## Etapa futura (fora deste PR)

Execução controlada sobre **cópia readonly** já validada (Converplast / Roda de Ouro) — procedimento separado, nunca no sistema publicado.
