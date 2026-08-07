# A02-A — Contrato do Motor de Qualidade (shadow)

**Status:** shadow — sem escrita, sem endpoint público, sem correção persistente.  
**Branch:** `feat/a02a-data-quality-shadow`  
**Base:** `feat/a01a-canonical-metrics-shadow`  
**Serviço:** `backend/services/data_quality_service.py`

## Objetivo

Analisar registros, agregar inconsistências, calcular **IQB (0–100)**, propor normalizações **em memória** e emitir sugestões — **sem** alterar dados originais nem expor PII.

## Assinatura

```python
service = DataQualityService(db)
resultado = service.analyze(
    client_id=2,
    periodo_inicio="2026-01",
    periodo_fim="2026-06",
    profile=DataQualityProfile(centro_custo_aplicavel=True, cid_aplicavel=True),
    reference_date=date(2026, 6, 20),
)
```

- `client_id` obrigatório (`> 0`), sem fallback.
- Período: mesma validação `YYYY-MM` do `MetricService`.
- Uploads auditados **independentemente** dos atestados (inclui zero eventos).
- Sessão não mutada; nenhuma escrita.

## Status por dimensão/campo

`avaliado` | `nao_aplicavel` | `indisponivel` | `nao_avaliado`

- Aplicável e ausente → **penaliza** (não melhora a nota).
- Explicitamente não aplicável (`DataQualityProfile`) → não penaliza; **redistribui** peso.
- Ausência total **não** remove dimensão automaticamente.

Saída IQB inclui `pesos_originais`, `pesos_efetivos`, `dimensoes_nao_aplicaveis`, `metodologia_redistribuicao`.

## Identidade

- **Por evento:** matrícula / CPF / só nome / sem id.
- **Por trabalhador aproximado:** melhor chave por identidade interna (base do IQB).
- Fragmentação documentada; sem fuzzy matching.

## Uploads e competência

- `multiplos_uploads_competencia` / `possivel_reupload` / `duplicidade_nao_confirmada`
- **Não** equivale a duplicidade confirmada (hash indisponível no schema).
- Períodos inválidos aparecem em `periodos_invalidos` mesmo com janela válida.

## Privacidade

Guard estruturado anti-PII do A01. Sem nome/CPF/matrícula/chave/CID individual.

## Não implementado

Correção automática, dicionário persistente, migration, cadastro mestre, IA, dashboard, endpoint, prevenção de reupload.
