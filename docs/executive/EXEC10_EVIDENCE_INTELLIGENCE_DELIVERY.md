# EXEC-10 — BioMed Evidence Intelligence™ Delivery

**Branch:** `cursor/exec10-evidence-intelligence-f8f5`  
**Status:** Draft · sem merge · sem deploy · sem produção · flags OFF  
**Base:** EXEC-09 Decision Experience

---

## Missão

Mostrar **por que** a recomendação merece confiança.  
Não cria novas análises — reapresenta evidências já existentes.

## As oito seções

1. Evidence Summary  
2. Evidence Sources  
3. Evidence Timeline  
4. Evidence Quality  
5. Evidence Confidence (Alta / Média / Baixa)  
6. Evidence Limitations  
7. What We Still Need  
8. Executive Conclusion (≤3 frases)

## Fluxo

Abertura → Decisão → **“Como sabemos disso?”** → Evidence Intelligence → Voltar à decisão.

## Valor agregado

O CEO entende a sustentação da decisão sem abrir relatório técnico: fontes, trajetória, qualidade, confiança, limites e o que ainda falta.

## Justificativa de UX

- Mesma identidade premium (espaço, tipografia, poucas cores).  
- Pergunta única: *Como sabemos disso?*  
- Sem venda, sem consultoria, sem CTA comercial.

## Controles

- Flag `ENABLE_EXECUTIVE_UI` OFF por padrão.  
- Sem migration · sem merge · sem deploy.  
- Parar após esta sprint — não iniciar EXEC-11.

## Testes

`tests/executive/test_exec10_evidence_intelligence.py` + suite `tests/executive/`.

## Screenshots

`tests/artifacts/executive_screenshots/exec10_*.png`
