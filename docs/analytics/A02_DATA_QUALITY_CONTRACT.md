# A02-A — Contrato do Motor de Qualidade (shadow)

**Status:** shadow — sem escrita, sem endpoint público, sem correção persistente.  
**Branch:** `feat/a02a-data-quality-shadow`  
**Base:** `feat/a01a-canonical-metrics-shadow` (@ `ce0bb99`)  
**Serviço:** `backend/services/data_quality_service.py`

## Objetivo

Analisar registros, agregar inconsistências, calcular **IQB** (0–100), propor normalizações **em memória** e emitir sugestões — **sem** alterar dados originais nem expor PII.

## Assinatura

```python
service = DataQualityService(db)
resultado = service.analyze(
    client_id=2,
    periodo_inicio="2026-01",
    periodo_fim="2026-06",
)
```

- `client_id` obrigatório (`> 0`), sem fallback.
- Período: mesma validação `YYYY-MM` do `MetricService`.
- Filtro: `Upload.client_id`.
- Sessão não mutada; nenhuma escrita.

## Saída (resumo)

- `iqb`, `classificacao`, `dimensoes`, `pesos`
- `completude`, `padronizacao_setor`, `centro_custo`, `identidade`
- `horas`, `dias_datas`, `cid`, `rastreabilidade`, `atualidade`
- `sugestoes`, `alertas`, `limitacoes`, `estrategia_identidade_futura`

Ver `A02_IQB_METHODOLOGY.md` e `A02_NORMALIZATION_CATALOG.md`.

## Privacidade

Reutiliza o guard estruturado anti-PII do A01 (`assert_no_pii_in_payload`).  
Proibido na saída: nome, CPF, matrícula, e-mail, telefone, documento, chave interna, CID por pessoa, linha original.

## Não implementado neste lote

Correção automática, dicionário persistente, migration, cadastro mestre, IA, dashboard, endpoint público, prevenção de reupload, plano de ação.
