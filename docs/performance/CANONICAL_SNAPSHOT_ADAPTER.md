# Canonical Snapshot Adapter

Conecta o `MetricService` (PR #5) ao `MetricSnapshot` do BioMed Performance Engine (Epic 2A), **sem duplicar fórmulas**.

## Contrato

```python
from backend.performance.canonical_snapshot_adapter import CanonicalSnapshotAdapter

adapter = CanonicalSnapshotAdapter(db)
bundle = adapter.build(
    client_id=2,
    periodo_inicio="2025-05",
    periodo_fim="2025-07",
    efetivo_trabalhadores=None,  # opcional
    iqb=None,                    # opcional (via DataQualityAdapter)
)
snapshot = bundle.snapshot
```

## Responsabilidades

1. Chamar `MetricService.compute(...)`.
2. Mapear agregados → `MetricSnapshot`.
3. Preservar fonte (`metric_service_canonical`) e metodologia de horas.
4. Separar `horas_perdidas_registradas` e `horas_perdidas_estimadas`.
5. Transferir qualidade da identidade (contagens agregadas).
6. Transferir cobertura de horas (`eventos_com_horas_* / eventos`).
7. Transferir eventos válidos/inválidos como limitações agregadas.
8. Nunca retornar PII; nunca expor chaves internas de identidade.

## Mapeamento

| Canônico | Snapshot |
|----------|----------|
| `eventos` | `eventos` |
| `trabalhadores_unicos` | `trabalhadores_unicos` |
| `dias_perdidos` | `dias_perdidos` |
| `horas_perdidas_registradas` | `horas_perdidas_registradas` |
| `horas_perdidas_estimadas` | `horas_perdidas_estimadas` |
| `duracao_media_dias` | `duracao_media` / `gravidade` |
| `eventos_por_100_trabalhadores` | `eventos_por_100` / `frequencia` |
| `dias_perdidos_por_trabalhador` | `dias_por_trabalhador` |
| `efetivo_trabalhadores` (input) | `headcount` |
| `qualidade.horas` | `metodologia_horas` |
| top setores / CID | `setores_criticos` / `grupos_cid` |

## Campos ausentes no contrato canônico

Quando não existirem no MetricService:

- retornar `None`;
- registrar limitação explícita;
- **não inferir silenciosamente**.

Exemplos: `recorrencia`, `afastamentos_longos`.

## Granularidade

A fonte é **mensal** (competência `YYYY-MM`). Completude = competências com upload / competências esperadas. Não há precisão diária.
