# EXEC-03 — Privacy Model

## Princípios

1. **Diretoria / apresentação executiva:** agregado por default · **sem PII**.
2. **Ranking nominal de trabalhador:** proibido no Command Center, Analytics e Presentation.
3. **Visão clínico-operacional autorizada:** superfície futura separada (RBAC); não misturar com deck de diretoria.
4. **Exportação executiva:** nenhum nome/CPF/matrícula por padrão.
5. **Small groups:** threshold `SMALL_GROUP_THRESHOLD=5` (MetricService).

## Recorrência

| Visão | Conteúdo |
|-------|----------|
| Executiva | Buckets 2+ / 3+ / 5+ · participação em eventos/dias/horas · **sem nomes** |
| Clínica autorizada | (preparado) identificação para acompanhamento ocupacional — não na apresentação |

## Guardrails técnicos

- `assert_no_pii_in_payload` no Command Center e Presentation.
- Chaves internas de trabalhador nunca expostas (tokens opacos só em agregação interna).
- Tenant isolation via `resolve_authorized_client`.

## Flags

```
ENABLE_EXECUTIVE_UI=false
ENABLE_EXECUTIVE_PRESENTATION=false
```

Não ligar em produção nesta etapa. Sem migration. Sem deploy.
