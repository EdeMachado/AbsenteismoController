# Absenteísmo Controller — Data Governance

## Camadas

| Camada | Conteúdo | Mutabilidade |
|--------|----------|--------------|
| **RAW** | Bytes do arquivo, nome, hash, metadados de upload | Imutável após gravação |
| **STANDARDIZED** | Linhas normalizadas + mapeamento versionado | Derivada; regenerável |
| **CURATED** | Agregados/métricas/insights inputs | Derivada; sem PII |

## Metadados RAW obrigatórios (alvo)

nome original, conteúdo, hash, data upload, usuário, cliente, competência informada, tamanho, formato, status de processamento.

## Identidade (política)

Prioridade futura: matrícula → pseudônimo analytics → CPF (camada médica restrita) → nome (fallback).  
**Não** migrar histórico no Épico 1. **Não** fuzzy matching automático.

## Qualidade

IQB (PR #6) e métricas canônicas (PR #5) operam em shadow/leitura.  
Normalização de rótulos em memória ≠ correção persistente.

## Reupload e idempotência

- Hash bruto / conteúdo normalizado / assinatura de layout.  
- Idêntico → bloquear.  
- Conteúdo igual → bloquear ou confirmação admin.  
- Possível atualização → diff de linhas + confirmação.  
- Sem dedupe silencioso do passado.

## LGPD (dados)

Minimização; agregação; supressão de grupos pequenos; separação clínico/administrativo; logs de exportação (Épico 4).
