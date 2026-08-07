# RC-1.1 — Product Consolidation

**Branch:** `cursor/rc1-product-consolidation-f8f5`  
**Status:** Draft · sem merge · sem deploy · sem produção

## Resumo executivo

Consolida EXEC-08→11B em uma **única jornada homologável** com identidade visual e nomenclatura unificadas.  
Não cria funcionalidades. Não altera Analytics, Decision, Evidence, Meeting, Financeiro, IA, Roadmap ou ORBIT.

## Preview

http://127.0.0.1:18083/preview/release-candidate

```bash
PYTHONPATH=/workspace SECRET_KEY=rc1-homolog \
  python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 18083
```

## Modo Comparação

- **Antes** — percepção fragmentada (módulos isolados / tipografia inconsistente)  
- **Depois** — plataforma consolidada RC-1

## Alterações realizadas (somente preview de homologação)

- Rota `/preview/release-candidate`
- CSS `biomed-rc1.css` alinhado à identidade EXEC-11
- Jornada única com nomes aprovados
- Remoção de duplicidades de texto entre Opening/Summary/Decision
- Densidade reduzida em Evidence / Decision Experience (sem mudar regra de negócio)
- Toggle Antes/Depois

## Decisões de UX

- Uma navegação linear Cover → Signature  
- Meta de reunião &lt; 5 minutos  
- Sem CTAs comerciais  
- Valores financeiros sempre ILUSTRATIVOS no dataset sintético

## Decisões de Design

- Tipografia BM Display + BM Sans  
- Paleta Brand / Teal / Sand  
- Sombras e radius únicos  
- Sem glow / sem estética de ERP

## Itens removidos (do preview consolidado)

- Painéis de auditoria técnica no fluxo CEO  
- Frases repetidas entre Opening e Summary  
- Nomenclaturas divergentes (“Product Audit”, “Excellence”, etc.) na jornada principal

## Itens consolidados

| Nome aprovado | Superfície |
|---------------|------------|
| Executive Cover | Capa |
| Executive Opening | Frase de estado |
| Executive Summary | Síntese |
| Decision | Card de decisão |
| Decision Experience | Evidência + roadmap |
| Evidence Intelligence | Como sabemos |
| Executive Closing | 4 perguntas |
| Executive Signature | Assinatura |

## Screenshots

`tests/artifacts/rc1_consolidation/rc1_*.png`

## PDF

`tests/artifacts/rc1_consolidation/BIOMED_RC1_CONSOLIDATION_REPORT.pdf`

## Testes

`tests/release/test_rc1_consolidation.py`

## Confirmação

Sem merge · sem deploy · sem produção · sem migration · sem nova API de negócio.  
Não inicia RC-1.2.
