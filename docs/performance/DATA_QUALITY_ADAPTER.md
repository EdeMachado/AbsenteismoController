# Data Quality Adapter (IQB)

Integra o `DataQualityService` (PR #6) ao pipeline shadow do Performance Engine **sem copiar a fórmula do IQB**.

## Contrato

```python
from backend.performance.data_quality_adapter import DataQualityAdapter

quality = DataQualityAdapter(db).build(
    client_id=2,
    periodo_inicio="2025-05",
    periodo_fim="2025-07",
)
# quality.iqb, quality.classificacao, quality.dimensoes, ...
```

## Transferência

Para o snapshot / análise shadow:

- IQB e classificação;
- dimensões e status;
- pesos originais e efetivos;
- metodologia de redistribuição;
- limitações;
- qualidade das horas (agregada);
- qualidade da identidade (contagens; sem PII);
- períodos inválidos;
- sinais de possíveis múltiplos uploads (alertas agregados).

## Privacidade

Apenas contagens e classificações. Não inclui nomes, CPF, matrícula nem amostras de linhas.
