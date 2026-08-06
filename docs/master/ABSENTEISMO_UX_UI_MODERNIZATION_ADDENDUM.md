# ADENDO AO MASTER PLAN — MODERNIZAÇÃO UX/UI

**Status:** obrigatório no Épico 2  
**Frente:** `UX/UI Modernization`  
**Data:** 2026-08-06  
**Escopo:** documentação de planejamento — sem implementação, merge ou deploy neste adendo

---

## 1. Objetivo

Modernizar o design visual e otimizar a experiência do usuário, com:

- padronização da identidade visual;
- simplificação da navegação;
- melhoria da usabilidade em todas as telas.

A frente é **parte integrante do Épico 2** (Biomed Intelligence Engine e Dashboard 2.0), não um épico separado.

---

## 2. Escopo UX

- auditar jornadas principais;
- consolidar menus;
- eliminar navegação duplicada;
- organizar arquitetura de informação;
- identificar páginas órfãs;
- reduzir quantidade de cliques;
- padronizar ações primárias e secundárias;
- criar breadcrumbs;
- melhorar filtros;
- melhorar estados vazios;
- criar estados de loading, sucesso e erro;
- melhorar mensagens de validação;
- exigir confirmação em ações destrutivas;
- melhorar acessibilidade;
- manter responsividade já validada (PR #3).

---

## 3. Escopo UI — design system leve

Criar biblioteca reutilizável com:

| Grupo | Itens |
|-------|--------|
| Fundação | paleta, tipografia, escala de espaçamento |
| Controles | botões, inputs, selects |
| Dados | tabelas, cards, badges, status |
| Overlay | modais, alertas, tooltips |
| Navegação | menus, cabeçalhos, breadcrumbs, filtros |
| Analytics | gráficos e estados de status |

---

## 4. Identidade visual

A interface deverá transmitir: **saúde, confiança, inteligência, segurança, tecnologia, clareza**.

### Evitar

- excesso de cores;
- gradientes decorativos;
- animações excessivas;
- ícones sem função;
- dashboards visualmente carregados;
- baixo contraste;
- textos pequenos;
- excesso de informações na mesma tela.

---

## 5. Gráficos (padronização)

Todo gráfico oficial / Dashboard 2.0 deverá padronizar:

- títulos e subtítulos;
- legenda;
- cores semânticas (sem julgamento clínico ou disciplinar de pessoas);
- unidade;
- tooltip;
- fonte dos dados;
- período;
- metodologia;
- estados sem dados;
- alertas de baixa qualidade (IQB);
- supressão de grupos pequenos (LGPD / k-anonimato operacional).

**Regra:** cores não atribuem julgamento clínico ou disciplinar a indivíduos.

---

## 6. Acessibilidade (progressivo)

Atender, progressivamente:

- contraste adequado;
- navegação por teclado;
- foco visível;
- labels em campos;
- mensagens associadas aos campos;
- tamanho mínimo de toque;
- leitura em telas menores;
- redução de movimento (`prefers-reduced-motion`);
- uso de cor sempre acompanhado de texto ou ícone.

---

## 7. Estratégia — sem redesign big bang

Ordem obrigatória:

1. inventário de componentes;
2. tokens visuais;
3. componentes-base;
4. **página-piloto**;
5. validação;
6. expansão gradual.

### Página-piloto recomendada

O **novo fluxo de ingestão inteligente** (Épico 1 — experimental), porque:

- é interface nova;
- não substitui o upload atual;
- permite validar o design system sem risco ao fluxo operacional da funcionária.

Depois, aplicar o design system aos módulos existentes no decorrer do Épico 2 (Dashboard 2.0 e telas legadas, de forma incremental).

---

## 8. Entrega esperada (Épico 2 — frente UX/UI)

| Entregável | Descrição |
|------------|-----------|
| Auditoria UX | Jornadas, fricções, órfãs, duplicidades |
| Mapa de navegação | IA consolidada + menus alvo |
| Design tokens | Cor, tipo, espaço, elevação, movimento |
| Biblioteca de componentes | CSS/JS leve, reutilizável |
| Página-piloto | Ingestão inteligente com DS aplicado |
| Screenshots | Desktop + mobile (artefatos locais) |
| Critérios de acessibilidade | Checklist progressivo |
| Plano de migração visual | Ordem de telas + flags |
| Testes responsivos | Manter baseline PR #3 |
| PR draft | Sem merge/deploy automático |

---

## 9. Fora de escopo deste adendo

- Implementação imediata do design system (fica no Épico 2).
- Substituição big-bang do frontend.
- Alterar upload legado como piloto.
- Merge ou deploy.

---

## 10. Referências cruzadas

- Plano do Épico 2: `ABSENTEISMO_EPIC_2_PLAN.md`
- Master plan: `ABSENTEISMO_MASTER_ARCHITECTURE_IMPLEMENTATION_PLAN.md` (§4 / Épico 2)
- Ingestão experimental (piloto): entrega Épico 1 / `docs/epic1/`
