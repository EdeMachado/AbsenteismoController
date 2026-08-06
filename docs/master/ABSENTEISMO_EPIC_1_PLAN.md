# Épico 1 — Fundação analítica e entrada de dados

## Objetivo

Consolidar PR #5 e PR #6 e construir a entrada de dados corporativa: conversor, preview, hash, prevenção de reupload, importação idempotente, preservação do arquivo bruto.

## Pré-requisitos

- #5 e #6 aprovados tecnicamente; merges autorizados conforme ordem do master plan.
- Backup validado antes de qualquer migration futura (não neste lote documental).

## Escopo

1. Arquitetura RAW / STANDARDIZED / CURATED (conceitual + contratos).  
2. Conversor inteligente determinístico (CSV/XLS/XLSX).  
3. Preview sem escrita + IQB estimado da planilha.  
4. Perfil de mapeamento versionado por cliente.  
5. Hash bruto + hash normalizado + assinatura de layout.  
6. Política de reupload (idêntico / conteúdo igual / atualização / complementar).  
7. Importação idempotente com simulação e transação.  
8. Modelo de identidade futura (documentado; **sem** migração histórica).

## Fora de escopo

- Dashboard novo / substituição de gráficos.  
- IA.  
- Deduplicação silenciosa de histórico.  
- PostgreSQL.  
- Deploy automático.

## Critérios de aceite

- Preview não grava.  
- Arquivo idêntico bloqueado por hash.  
- Rollback integral em erro de importação.  
- Tenant obrigatório.  
- Sem PII em preview para perfis não autorizados.  
- Testes listados no master plan §16.  
- PR draft; sem merge/deploy sem autorização.

## Backlog (itens)

| ID | Item | Prioridade |
|----|------|------------|
| E1-01 | Docs RAW/STD/CURATED | P0 |
| E1-02 | Serviço de ingestão + storage RAW | P0 |
| E1-03 | Detector de cabeçalho/aba | P0 |
| E1-04 | Motor de mapeamento + confiança | P0 |
| E1-05 | Preview API (teste/admin) | P0 |
| E1-06 | IQB do arquivo (reuso A02) | P1 |
| E1-07 | Perfil de mapeamento versionado | P1 |
| E1-08 | Hash bruto/normalizado | P0 |
| E1-09 | Política reupload | P0 |
| E1-10 | Import idempotente + dry-run | P0 |
| E1-11 | Testes sintéticos §16 | P0 |
| E1-12 | Plano de migration futura (só doc) | P2 |

## Dependências

- A01 MetricService / A02 DataQuality (PRs #5/#6).  
- Auth/tenant (PR #4) fortemente recomendado antes de APIs de upload novas.
