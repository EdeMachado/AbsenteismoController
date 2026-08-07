# EXEC-03 — Presentation Architecture

## Rotas

| Superfície | Path | Flag |
|------------|------|------|
| Command Center | `/executive` | `ENABLE_EXECUTIVE_UI` |
| Presentation (nova) | `/executive/presentation` | `ENABLE_EXECUTIVE_UI` **e** `ENABLE_EXECUTIVE_PRESENTATION` |
| API deck | `/api/executive/presentation` | idem |
| **Legado** | `/apresentacao` | inalterado |

Ambas as flags **OFF** por default. Não apagar apresentação legada.

## Composer

`compose_presentation(payload)` em `backend/executive/presentation.py`:

1. Percorre 18 `SLIDE_DEFS`.
2. Avalia `required` contra payload.
3. **Omite** slides sem dados (não cria slides vazios).
4. Cada slide analítico: gráfico (quando houver) · título · leitura · recomendação · confiança · fonte/metodologia.
5. `privacy.pii_excluded=true` · sem ranking nominal.

## Slides (estrutura)

1. Resumo executivo  
2. KPIs principais  
3. Evolução do absenteísmo  
4. Impacto em dias e horas  
5. Custo do absenteísmo (**obrigatório quando calculável**)  
6. Principais causas / CID  
7. Setores críticos  
8. Recorrência (agregada)  
9. Afastamentos prolongados  
10. Padrões temporais  
11. Qualidade dos dados  
12. Atuação BioMed  
13. Resultado observado  
14. Condicionantes empresariais  
15. BioMed Intelligence  
16. Plano de Ação  
17. Prioridades próximo ciclo  
18. Metodologia / limitações  

## Exportação

- Sprint: **modo tela** (HTML + teclado ←/→).
- PDF / PowerPoint: estrutura de slides reutilizável; preservar exportadores legados quando possível — não reimplementar biblioteca nesta sprint.

## Frontend

- `frontend/executive_presentation.html`
- `frontend/static/js/executive/presentation.js`
