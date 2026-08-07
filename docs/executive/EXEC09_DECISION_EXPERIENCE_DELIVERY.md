# EXEC-09 — BioMed Executive Decision Experience™ Delivery

**Branch:** `cursor/exec09-decision-experience-f8f5`  
**Status:** Draft · sem merge · sem deploy · sem produção · flags OFF  
**Base:** EXEC-08 first experience

---

## Missão

Transformar o card “Entender esta decisão” em uma **conversa visual completa** (não modal, não popup, não relatório).

## As seis perguntas

1. Qual é o problema?  
2. Como sabemos disso?  
3. Quanto isso custa?  
4. Quanto podemos economizar?  
5. Como resolver?  
6. Qual deve ser o primeiro passo?  

Contrato: `decision_experience.six_answers` + blocos 1–8 na UI.

## Antes → Depois

| Antes (EXEC-08) | Depois (EXEC-09) |
|-----------------|------------------|
| Modal curto com título/descrição | View full-page Decision Experience |
| Sem evidência visual | Evidence: indicadores + barras |
| Sem premissa financeira explícita | Business Impact com REAL/ESTIMADO/ILUSTRATIVO/NÃO INFORMADO |
| Uma linha de ação | Até 3 recomendações + roadmap 30/90/180/365 |
| Sem confiança explícita | Evidence Confidence Alta/Média/Baixa |

## Valor agregado

O CEO sai da experiência capaz de repetir: problema, impacto, prioridade, custo, benefício e primeiro passo — sem caçar slides.

## Justificativa de UX

- Continuação da identidade EXEC-08 (espaço, tipografia, poucas cores).  
- Troca de contexto por **view**, não modal (respiração de reunião).  
- Números financeiros só com evidência; omissão honesta > invenção.  
- Rodapé ORBIT™ discreto, sem CTA comercial.

## Fora de escopo

ORBIT completo · Innovation · Health Transformation · oferta comercial.

## Testes

Suite `tests/executive/` — incluir `test_exec09_decision_experience.py`.

## Screenshots

`tests/artifacts/executive_screenshots/exec09_*.png`

## Parar

Fim desta sprint. Não iniciar EXEC-10.


## Screenshots capturados

| Arquivo | Conteúdo |
|---------|----------|
| `exec09_before_abertura_1440x900.png` | Antes — Abertura (EXEC-08) |
| `exec09_before_abertura_1920x1080.png` | Antes — Abertura 1920 |
| `exec09_flow_cta_visible_1440x900.png` | CTA "Entender esta decisão" |
| `exec09_after_decision_top_1440x900.png` | Depois — topo Decision Experience |
| `exec09_after_decision_full_1440x900.png` | Depois — página completa |
| `exec09_after_decision_1920x1080.png` | Depois — 1920 |
| `exec09_after_decision_390x844.png` | Depois — mobile |
| `exec09_flow_roadmap_1440x900.png` | Roadmap + Expected Results |
| `exec09_flow_confidence_footer_1440x900.png` | Evidence Confidence |
| `exec09_flow_orbit_footer_1440x900.png` | Rodapé ORBIT™ (sem CTA comercial) |
| `exec09_flow_back_abertura_1440x900.png` | Voltar à abertura |

## Critério de sucesso (CEO)

| Pergunta | Onde responde |
|----------|---------------|
| Problema | Header + `six_answers.problem` |
| Impacto | Header impact + Business Impact |
| Prioridade | Priority label |
| Custo | Business Impact · Quanto custa hoje? (REAL/ESTIMADO/ILUSTRATIVO/NÃO INFORMADO) |
| Benefício | Savings potential + Expected Results |
| Primeiro passo | Destaque sob Recommendations + roadmap 30 dias |

## Controles

- Flag `ENABLE_EXECUTIVE_UI` permanece OFF por padrão.
- Sem migration, sem merge, sem deploy, sem produção.
- Sem ORBIT comercial / Innovation / Health Transformation.
