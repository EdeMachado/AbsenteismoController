# RC-1.4 — Executive Presentation Premium

**Branch:** `cursor/rc14-executive-presentation-premium-f8f5`  
**HEAD:** `514a25a1caf0bfd2b12d1de87292f4f330bdcc78`
**Status:** Draft · sem merge · sem deploy · sem produção

## Preview

`/preview/executive-presentation-rc` — dataset sintético, sem login, premissa ILUSTRATIVA.

## As 4 perguntas

1. Quanto estamos perdendo?  
2. Por que estamos perdendo?  
3. Quanto podemos melhorar/economizar?  
4. O que precisamos decidir agora?

## Slides mantidos (estrutura premium)

Cover · Estado · Impacto financeiro · Onde está o problema · O que mais afasta · Recorrência · Quando (se houver) · O que mudou · Atuação BioMed · Quanto podemos melhorar (se válido) · E se nada mudar (se válido) · 3 prioridades · Roteiro 30/90/180 · Decisão · Encerramento

## Slides removidos / fundidos (vs EXEC-03 18 slides)

| Removido / fundido | Destino |
|--------------------|---------|
| resumo + kpis genéricos | Cover + Estado + Financeiro |
| impacto_dias_horas + custo | Impacto financeiro (único) |
| qualidade / metodologia / intelligence genérica | Omitidos do modo CEO |
| afastamentos prolongados | Fora do caminho crítico CEO |
| plano_acao + prioridades duplicados | As 3 prioridades |
| atuacao + resultado + condicionantes | Atuação BioMed (fundido) |

## Tempo estimado

Modo CEO: **≈ 4–5 minutos** (omissão automática reduz ainda mais quando falta evidência).

## Financeiro

- Fórmula: **HORAS PERDIDAS × CUSTO HORA**
- Premissas: REAL · ESTIMADO · ILUSTRATIVO · NÃO INFORMADO
- Sem inventar custo hora; demonstração usa ILUSTRATIVO marcado
- Sem double-count dias+horas no valor financeiro

## Evidência

Badge por slide: Confiança alta · Confiança moderada · Evidência insuficiente.  
Slides sem evidência são **omitidos**, não esvaziados.

## Screenshots / PDF

`tests/artifacts/rc14_presentation/` — rc14_*.png · rc14_full.pdf

## Testes

`tests/release/test_rc14_executive_presentation.py` · regressão EXEC-03 presentation

## Limitações

- Preview sintético; PDF gerado a partir do preview (não substitui exportadores legados PPTX)
- Mobile funcional, otimizado para desktop/tablet em sala
- Sem CTA comercial

## Confirmação

Sem merge · sem deploy · sem produção. Não inicia RC-1.5.
