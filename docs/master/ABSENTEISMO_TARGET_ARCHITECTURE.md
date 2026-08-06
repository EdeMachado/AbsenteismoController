# Absenteísmo Controller — Target Architecture

## Visão

Plataforma corporativa de inteligência ocupacional, preservando a operação atual da funcionária e os dados de produção.

## Camadas de dados

```text
RAW              → arquivo e bytes exatamente como recebidos
STANDARDIZED     → colunas/tipos/identidade canônicos (conversão)
CURATED          → fatos agregados para métricas, gráficos, insights
```

O bruto **nunca** é sobrescrito pela versão convertida.

## Pipeline alvo

```text
Upload bruto (RAW)
  → Conversor determinístico + perfil de mapeamento por cliente
  → Preview + IQB do arquivo (sem escrita)
  → Hash bruto + hash normalizado + assinatura de layout
  → Política de reupload / idempotência
  → Persistência transacional
  → MetricService (canônico) + DataQualityService (IQB)
  → Intelligence Engine (métricas oficiais)
  → Dashboards (somente consumo)
  → Motor de regras → Biomed Insight → Plano de ação
```

## Separação de responsabilidades

| Camada | Responsabilidade |
|--------|------------------|
| Frontend | Exibir; não calcular regras de negócio oficiais |
| Routers | HTTP, auth, tenant |
| Services | Domínio (métricas, qualidade, recorrência, insight) |
| Repositories | Acesso a dados |
| Schemas | Contratos tipados |

Extração **progressiva** de `main.py` — sem rewrite big-bang.

## Serviços já iniciados (shadow)

- `metric_service.py` (PR #5)
- `data_quality_service.py` (PR #6)
- `shadow_compare.py` (conferência local)

## Serviços futuros (épicos)

`recurrence_service`, `trend_service`, `severity_service`, `frequency_service`, `pareto_service`, `comparison_service`, `intelligence_engine`, import/converter/hash services.

## Multi-tenant

Todo cálculo e toda importação recebem `client_id` explícito. Sem fallback. Sem inferência pelo frontend.

## Privacidade

Agregados; supressão de grupos pequenos; PII fora de analytics/IA; perfis RH/SST/médico/diretoria/admin.
