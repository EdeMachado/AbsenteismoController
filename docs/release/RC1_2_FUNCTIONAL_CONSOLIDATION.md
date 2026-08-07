# RC-1.2 — Functional Consolidation & Micro-UX

**Branch:** `cursor/rc12-functional-consolidation-f8f5`  
**HEAD:** `f8d111ef6e5db02ac6635066db05b8af89a765eb`
**Status:** Draft · sem merge · sem deploy · sem produção

## Preview

http://127.0.0.1:18083/preview/release-candidate-functional

## Atritos encontrados

- Mensagens com linguagem de sistema (“payload”)
- Escape incompleto (decisão → abertura)
- Hash do browser sem sincronizar view
- Falta de foco após troca de view
- Loading sem estrutura (risco de layout shift)
- 403 tratado como erro genérico
- Estados vazios / erro / custo NÃO INFORMADO pouco explícitos no preview
- CTAs de navegação do chrome competindo (Antes/Depois herdados do RC-1.1 no fluxo funcional)

## Atritos corrigidos

- Microcopy humano em erros/indisponibilidade
- Escape: Evidence → Decision → Opening
- `hashchange` sincroniza views
- Focus no main após troca
- Skeleton discreto no loading
- 401 → login; 403 → mensagem sem logout
- Preview com empty / error / financial NÃO INFORMADO / loading
- CTAs padronizados: Entender esta decisão · Como sabemos disso? · Voltar à decisão · Continuar
- Progress “onde você está”

## CTAs removidos/consolidados

- Removidos do fluxo funcional: Antes / Depois (permanecem no RC-1.1 visual)
- 1 CTA primário por superfície crítica (Decision / Evidence)
- Secundário apenas Voltar / Continuar

## Testes

- `tests/release/test_rc12_functional.py` (rota + jornada sintética)
- Suíte executiva relevante

## Screenshots

`tests/artifacts/rc12_functional/rc12_*.png`

## Limitações

- Homologação sintética; não altera Analytics/ORBIT/Opportunity
- Sem mudança de regra de negócio ou modelo financeiro

## Confirmação

Sem merge · sem deploy · sem produção. Não inicia RC-1.3.
