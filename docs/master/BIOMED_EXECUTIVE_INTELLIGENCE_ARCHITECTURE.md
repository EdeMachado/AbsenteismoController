# BioMed Executive Intelligence — Arquitetura Definitiva do Produto

**Nome de produto:** BioMed Executive Intelligence *(Command Center)*  
**Documento:** arquitetura e planejamento — **sem implementação**  
**Status:** proposta de arquitetura (Epic 3 — visão de produto)  
**Data:** 2026-08-06  
**Escopo deste arquivo:** somente documentação  

> **ATENÇÃO:** Este documento **não autoriza** código, migration, alteração de banco, frontend, backend, commit, PR, merge ou deploy.  
> Produção, SQLite vivo, usuários, senhas e permissões permanecem intocados.

---

## 0. Contexto e premissas

### 0.1 O que já existe (shadow, não integrado ao dashboard)

| PR | Capacidade | Estado |
|----|------------|--------|
| #4 | Auth / tenant / guard | shadow / draft |
| #5 | Canonical Metrics (`MetricService`) | shadow |
| #6 | IQB (`DataQualityService`) | shadow |
| #8 | Intelligent Ingestion | shadow |
| #10 | Performance Engine + adaptadores canônicos (2A/2A-B) | shadow |

Nenhum desses PRs está no dashboard publicado. A operação atual (uploads, clientes, usuários, produção) permanece.

### 0.2 Nova visão de produto

O produto **deixa de ser** “Dashboard de Absenteísmo”.  
Passa a ser **BioMed Executive Intelligence** (Command Center): plataforma de decisão corporativa em saúde ocupacional e desempenho assistencial BioMed.

O **absenteísmo** torna-se **uma dimensão** entre várias (qualidade de dados, cobertura, execução, efetividade, risco, plano de ação, ROI).

### 0.3 Princípios de experiência

Referências de qualidade (não cópia literal de marca):

- Power BI Premium / Microsoft Fabric / Azure Dashboard — clareza analítica e hierarquia  
- Apple HIG / Material Design 3 / IBM Carbon — densidade controlada, acessibilidade  
- Linear / Stripe Dashboard / Notion — foco em decisão, pouco ruído  

**Regras duras de UX:**

- interface premium; pouca informação por tela; foco em decisão;  
- zero telas poluídas; gráficos **fora** da Home;  
- fatos ≠ hipóteses ≠ recomendações;  
- validação humana obrigatória para ações.

### 0.4 Princípios de IA (não negociáveis)

A IA **nunca** poderá:

- inventar causalidade, ROI, produtividade, resultados, diagnóstico ou clínica;  
- apresentar hipótese como fato;  
- substituir prontuário ou julgamento médico.

Toda hipótese deve ser marcada explicitamente como **hipótese**, com limitações e necessidade de validação humana.

---

## 1. Arquitetura completa

### 1.1 Visão em camadas

```text
┌─────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                             │
│  Command Center · Analytics · Situation Room · Action · etc.    │
│  (HTML/JS ou futuro SPA — só consome contratos; não calcula KPI)│
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP + auth + tenant (PR #4)
┌───────────────────────────────▼─────────────────────────────────┐
│  APPLICATION LAYER                                              │
│  Orchestrators / Use-cases / Flags / Audit trail                │
└───────┬─────────────┬─────────────┬─────────────┬───────────────┘
        │             │             │             │
┌───────▼──────┐ ┌────▼─────┐ ┌─────▼─────┐ ┌────▼──────────────┐
│ ANALYTICS    │ │ ENGINE   │ │ AI LAYER  │ │ ACTION / WORKFLOW │
│ MetricService│ │ Perf.    │ │ Coordena- │ │ Plano · Decisão  │
│ IQB · Trends │ │ BioMed   │ │ dora      │ │ Acompanhamento    │
│ Heat/Pareto  │ │ ROI*     │ │ Briefs    │ │ Condicionantes    │
└───────┬──────┘ └────┬─────┘ └─────┬─────┘ └────┬──────────────┘
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼──────────────┐
│  ADAPTERS                                                       │
│  Canonical Snapshot · DQ · Window · Legacy bridge (read-only)   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  STORAGE LAYER                                                  │
│  RAW files · SQLite (tenant) · aggregates cache (futuro)        │
│  Structured Clinical Interview (não-prontuário)                 │
└─────────────────────────────────────────────────────────────────┘
```

\* ROI somente com premissas econômicas explícitas e auditáveis; sem custos → `ROI_NAO_CALCULAVEL`.

### 1.2 Camadas de dados (inalteradas na essência)

```text
RAW           → arquivo original preservado
STANDARDIZED  → colunas/tipos/identidade canônicos
CURATED       → fatos agregados (métricas, gráficos, insights)
```

O bruto nunca é sobrescrito. Analytics e IA consomem **CURATED** (agregados), não linhas clínicas livres.

### 1.3 Pipeline alvo do sistema

```text
Ingestão inteligente (PR #8)
  → MetricService canônico (PR #5)
  → DataQuality / IQB (PR #6)
  → Performance Engine (PR #10)
  → Rule Engine determinístico (insights)
  → AI Coordinator (narrativa sobre fatos já calculados)
  → Action Plan + Conditionants
  → Presentation (Command Center / Analytics / Situation Room)
  → Simulator (cenários hipotéticos rotulados)
```

### 1.4 Separação de responsabilidades

| Camada | Faz | Não faz |
|--------|-----|---------|
| **Presentation** | Layout, filtros de UI, estados vazios/loading, navegação | Recalcular KPIs oficiais; inventar ROI |
| **Application** | Orquestrar casos de uso; feature flags; auditoria de acesso | Fórmulas de métricas |
| **Analytics** | Métricas canônicas, IQB, séries, pareto, sazonalidade | Diagnóstico clínico |
| **Engine** | Efetividade, score, cobertura, confiança, ROI condicionado | Causalidade automática |
| **AI Layer** | Briefs, hipóteses rotuladas, prioridades sugeridas | Inventar números ou clínica |
| **Action** | Ciclo de vida da ação e decisão empresarial | Executar mudança operacional sozinha |
| **Adapters** | Traduzir contratos canônicos → motores | Duplicar fórmulas |
| **Storage** | Persistência tenant-aware; RAW imutável | Expor PII a analytics |

### 1.5 Multi-tenant e segurança

- Todo cálculo e toda leitura recebem `client_id` explícito (sem fallback).  
- Guards PR #4 obrigatórios antes de qualquer HTTP novo.  
- Agregados; supressão de grupos pequenos; anti-PII em saídas de engine/IA.  
- Perfis: RH / SST / médico / diretoria / admin — com campos clínicos estruturados só para papéis autorizados.

### 1.6 Feature flags (padrão shadow → gradual)

```text
ENABLE_BIOMED_COMMAND_CENTER=false
ENABLE_ANALYTICS_CENTER=false
ENABLE_AI_COORDINATOR=false
ENABLE_ACTION_PLAN_V2=false
ENABLE_BIOMED_PERFORMANCE_ENGINE=false   # já existe (PR #10)
ENABLE_SITUATION_ROOM=false
ENABLE_CLINICAL_CARD=false
ENABLE_EXECUTIVE_SIMULATOR=false
```

Nenhuma flag ligada em produção sem autorização, backup e critérios de aceite.

---

## 2. Mapa de módulos

| # | Módulo | Nome | Função | Entrada principal | Saída |
|---|--------|------|--------|-------------------|-------|
| 1 | ECC | Executive Command Center | Home de decisão | Agregados + IQB + Performance + alertas | Cards executivos |
| 2 | AC | Analytics Center | Todos os gráficos | Métricas canônicas | Visualizações + drill-down |
| 3 | AIC | IA Coordenadora | Briefs automáticos diários | Fatos/engine/regras | Brief + hipóteses + plano sugerido |
| 4 | PAI | Plano de Ação Inteligente | Ciclo insight→ação→resultado | Insights + decisões | Ações rastreáveis |
| 5 | PBM | Performance BioMed | Cobertura/execução/adesão/resultado/efetividade/confiança | PR #10 + inputs explícitos | Score e limitações |
| 6 | SDS | Sala de Situação | Painel único premium | Alertas + timeline + mapa + plano | Visão situacional |
| 7 | FCE | Ficha Clínica Estruturada | Entrevista clínica estruturada | Formulário controlado | Apoio ao plano (**não** prontuário) |
| 8 | SEX | Simulador Executivo | Cenários hipotéticos | Premissas explícitas | ROI/economia **simulados** rotulados |
| 9 | UX | UX/UI Modernization | Design system + tokens | — | Consistência visual |
| 10 | ARCH | Arquitetura / Platform | Camadas, adapters, flags, observabilidade | — | Governança técnica |

### 2.1 Detalhamento dos módulos de produto

#### Módulo 1 — Executive Command Center (Home)

**Mostrar apenas:**

- Índice Geral de Saúde Corporativa  
- Risco Atual  
- Tendência  
- Performance BioMed  
- IQB  
- ROI *(ou `NAO_CALCULAVEL`)*  
- Alertas  
- Plano prioritário  

**Proibido na Home:** gráficos grandes, tabelas densas, listas operacionais, widgets decorativos.

#### Módulo 2 — Analytics Center

Reorganiza o dashboard atual. **Todo gráfico oficial vive aqui.**

Heatmap · Timeline · Radar · Pareto · Treemap · Benchmark · Distribuições · Drill-down · Filtros inteligentes · Comparativos · Sazonalidade · Severidade · Recorrência · Setores · Centro de custo · CID (agregado).

Fonte exclusiva: **métricas canônicas** (+ qualidade/IQB como metadado). Frontend não recalcula.

#### Módulo 3 — IA Coordenadora

**Não é chatbot.** Sem caixa de conversa.

Rotina automática (ex.: diária / pós-upload / sob demanda controlada) produz:

1. Executive Brief  
2. Resumo Executivo  
3. Análise Técnica  
4. Hipóteses *(rotuladas)*  
5. Limitações  
6. Plano de ação sugerido  
7. Prioridades  
8. Riscos  
9. Oportunidades  

Contrato de entrada: apenas payloads agregados já calculados (regras + engine).  
Contrato de saída: narrativa estruturada com `fato | interpretacao | hipotese | limitacao | recomendacao`.

#### Módulo 4 — Plano de Ação Inteligente

Cada insight materializável gera / atualiza:

ação · responsável · prioridade · prazo · status · impacto esperado · resultado observado · barreiras · decisão empresarial · revisão · histórico.

Status sugeridos: apresentada · aceita · aceita_com_ajustes · adiada · recusada · executada · concluída · cancelada · pendente.

Validação humana obrigatória antes de tratar como “decisão da empresa”.

#### Módulo 5 — Performance BioMed

**Não medir:** consultas soltas, volume bruto de atendimentos como sucesso.

**Medir (auditável):**

Cobertura · Execução · Adesão · Resultado · Efetividade · Confiança · Performance BioMed (score composto com pesos efetivos e cobertura).

Reutilizar contratos do PR #10 (shadow → integração gradual). Ausência de produtividade BioMed validada → dimensão não avaliada (nunca nota neutra inventada).

#### Módulo 6 — Sala de Situação

Uma tela. Premium. Sem poluição.

Componentes: alertas · timeline · mapa *(agregado geográfico/setor, se houver)* · heatmap · faixa IA (brief curto) · plano de ação prioritário · indicadores-chave.

Densidade baixa; hierarquia forte; refresh controlado.

#### Módulo 7 — Ficha Clínica Estruturada

**Não existe:** prontuário, exames, anexos, documentos do funcionário.

**Existe:** entrevista clínica estruturada (campos controlados, tipados, auditáveis), **apenas** como apoio ao Plano de Ação.

Nunca substitui prontuário médico. Nunca armazena exames. LGPD e papel/perfil rigorosos. Preferência por agregação nas demais telas.

#### Módulo 8 — Simulador Executivo

Simula (sempre rotulado **SIMULADO / HIPOTÉTICO**):

- redução de absenteísmo / severidade / CID agregado;  
- ergonomia, treinamentos, campanhas;

e mostra ROI · economia · dias/horas recuperados · cenários.

Sem premissa econômica explícita → não inventar ROI “observado”.

#### Módulo 9 — UX/UI Modernization

Definir e versionar: paleta · tipografia · ícones · cards · componentes · espaçamentos · grid · responsividade · dark mode **futuro** · design system · tokens · biblioteca gráfica · animações · microinterações.

Alinhar ao adendo já existente (`ABSENTEISMO_UX_UI_MODERNIZATION_ADDENDUM.md` nas branches de docs).

#### Módulo 10 — Arquitetura de plataforma

Governança das camadas (§1), adapters, engines, AI layer, observabilidade, flags, testes de contrato, rollout/rollback.

---

## 3. Fluxo completo do sistema

```text
[1] Upload / reupload (Ingestão inteligente)
        ↓
[2] Preview + IQB do arquivo (sem escrita até confirmar)
        ↓
[3] Persistência RAW + STANDARDIZED (idempotente)
        ↓
[4] MetricService.compute (canônico, tenant)
        ↓
[5] DataQualityService.analyze (IQB)
        ↓
[6] PerformanceShadow/Service (janelas comparáveis)
        ↓
[7] Rule Engine → Insights determinísticos
        ↓
[8] AI Coordinator → Brief (narrativa sobre [4–7])
        ↓
[9] Action Plan (humano valida / decide)
        ↓
[10] Acompanhamento (status, barreiras, resultado observado)
        ↓
[11] Presentation:
        Home (ECC) | Analytics | Situation Room | Simulator
```

### 3.1 Fluxo de decisão (humano no centro)

```text
Fato agregado → Insight (regra) → Hipótese (IA, opcional)
     → Ação sugerida → Decisão empresarial
     → Execução → Resultado observado → Revisão
```

Nenhuma seta implica causalidade automática.

### 3.2 Fluxo de qualidade

```text
IQB baixo → limitações propagadas → score INSUFICIENTE possível
         → Analytics exibe aviso → IA reduz confiança → Home destaca risco de dados
```

---

## 4. Mapa de navegação

### 4.1 Informação architecture (IA)

```text
BioMed Command Center
├── Home (Executive Command Center)          [default]
├── Analytics Center
│   ├── Visão geral analítica
│   ├── Absenteísmo & severidade
│   ├── Setores / CC / CID (agregado)
│   ├── Sazonalidade & comparativos
│   └── Qualidade de dados (IQB)
├── Sala de Situação
├── Performance BioMed
├── Plano de Ação
│   ├── Prioridades
│   ├── Kanban / lista
│   └── Histórico & revisões
├── Briefs da IA (somente leitura + export)
├── Ficha Clínica Estruturada                [perfil restrito]
├── Simulador Executivo
├── Ingestão / Uploads
└── Administração (usuários, tenant, flags)  [admin]
```

### 4.2 Regras de navegação

- Home **não** embute Analytics.  
- “Ver detalhes” leva ao Analytics ou à Sala com contexto (período, dimensão).  
- Briefs da IA não abrem chat.  
- Ficha Clínica fora do fluxo executivo padrão; deep-link só a partir de ação autorizada.  
- Breadcrumbs obrigatórios fora da Home.  
- Mobile: Home e alertas primeiro; gráficos complexos degradam para cards/resumo.

### 4.3 Transição do dashboard legado

1. Dashboard atual permanece atrás de flag/legado.  
2. Gráficos migram um a um para Analytics Center (fonte canônica).  
3. Home nova substitui a landing apenas com flag + aceite.  
4. Remoção do legado só após paridade e treinamento.

---

## 5. Design System

### 5.1 Tom

Saúde · confiança · inteligência · segurança · clareza.  
Evitar: excesso de cor, glow, pills decorativas, dashboards densos, tipografia genérica de “AI purple”.

### 5.2 Fundação (tokens)

| Token group | Direção |
|-------------|---------|
| **Cor** | Neutros frios + 1 acento institucional + semântica (ok / atenção / risco / info) sem julgamento clínico individual |
| **Tipo** | Display expressivo (1 família) + texto UI legível (1 família); evitar Inter/Roboto/Arial como identidade |
| **Espaço** | Escala 4/8 (4, 8, 12, 16, 24, 32, 48, 64) |
| **Raio** | Conservador (4–12); sem “cardificar” tudo |
| **Sombra** | Mínima; hierarquia por espaço e tipografia |
| **Ícones** | Linha, funcionais; nunca emoji |

### 5.3 Componentes mínimos

- App shell (nav, header, tenant badge)  
- KPI card executivo (valor, Δ, estado, limitação)  
- Alert strip  
- Data table  
- Filter bar  
- Status badge (ação / IQB / score)  
- Empty / loading / error  
- Chart frame (título, unidade, fonte, período, metodologia, IQB)  
- Action row  
- Brief document layout  

### 5.4 Biblioteca gráfica

Uma lib oficial (ex.: ECharts ou Chart.js — decisão na implementação).  
Todo gráfico oficial exige: título, subtítulo, unidade, tooltip, fonte, período, metodologia, estado sem dados, aviso IQB, k-anonimato.

### 5.5 Motion

2–3 movimentos intencionais: entrada de cards da Home, transição de rota, atualização suave de KPI. Sem ruído.

### 5.6 Dark mode

**Futuro.** Tokens preparados; não bloquear MVP claro.

---

## 6. Arquitetura UX

### 6.1 Hierarquia de telas

| Prioridade | Tela | Densidade | Objetivo |
|------------|------|-----------|----------|
| P0 | Home ECC | Muito baixa | Decidir o que importa hoje |
| P0 | Plano de Ação | Baixa | Agir e acompanhar |
| P1 | Sala de Situação | Baixa–média | Situação em uma tela |
| P1 | Performance BioMed | Baixa | Auditar efetividade |
| P2 | Analytics Center | Média (controlada) | Explorar |
| P2 | Briefs IA | Documento | Ler e exportar |
| P3 | Simulador | Média | Planejar cenários |
| P3 | Ficha Clínica | Formulário | Apoiar ação (restrito) |

### 6.2 Padrão “uma composição”

- Home = uma composição (não dashboard).  
- Cada seção = um propósito, um título, uma frase de apoio.  
- Cards só quando forem unidade de interação/decisão.  
- Hero/branding do produto nas superfícies promocionais internas (login/landing), não competindo com KPIs.

### 6.3 Estados obrigatórios

Vazio · loading · erro · IQB insuficiente · sem headcount · ROI não calculável · janelas não comparáveis · sem permissão.

### 6.4 Acessibilidade (progressivo)

Contraste, foco visível, teclado, labels, não depender só de cor.

---

## 7. Arquitetura IA

### 7.1 Papel

**Coordenadora**, não oráculo.  
Consome fatos e regras; produz narrativa e priorização **sugerida**.

### 7.2 Pipeline IA

```text
CURATED aggregates + Rule insights + Performance result + IQB
        → Prompt assembly (templates versionados)
        → Model (configurável; desligável)
        → Schema validation (JSON estruturado)
        → Hypothesis tagging + PII guard
        → Persist Brief (por tenant/dia)
        → Presentation (somente leitura)
```

### 7.3 Contrato de saída (obrigatório)

```json
{
  "executive_brief": "...",
  "resumo_executivo": "...",
  "analise_tecnica": "...",
  "fatos": ["..."],
  "interpretacoes": ["..."],
  "hipoteses": [{"texto": "...", "confianca": 0.0, "base": ["metric_id"]}],
  "limitacoes": ["..."],
  "plano_sugerido": [{"acao": "...", "prioridade": "...", "evidencias": []}],
  "prioridades": [],
  "riscos": [],
  "oportunidades": [],
  "exige_validacao_humana": true
}
```

### 7.4 Guardrails

| Proibido | Mitigação |
|----------|-----------|
| Inventar métricas | Só referenciar IDs presentes no payload |
| Causalidade | Linguagem de associação / hipótese |
| ROI inventado | Copiar status do engine (`NAO_CALCULAVEL` etc.) |
| Diagnóstico clínico | Fora do schema |
| PII | Guard + testes |
| Chat livre | Sem UI de conversa no MVP |

### 7.5 Fallback sem modelo

Se IA desligada: Brief gerado por **templates determinísticos** a partir das regras (qualidade inferior na prosa, mesma honestidade factual).

---

## 8. Roadmap de implementação

Ordem **técnica** (não cronograma de calendário). Cada fase = branch própria, testes, flag off, PR draft, parada antes de merge.

| Fase | Nome | Entrega | Depende de |
|------|------|---------|------------|
| **F0** | Governança docs | Este documento + alinhamento master plan | — |
| **F1** | Fundação segura | Integrar PR #4 em rotas novas | Auth |
| **F2** | Contratos canônicos vivos | Expor MetricService/IQB atrás de flags (read) | #5 #6 |
| **F3** | Design system leve | Tokens + shell + KPI card | UX addendum |
| **F4** | Command Center Home | Módulo 1 (só cards) | F2 F3 #10 adaptadores |
| **F5** | Analytics Center v1 | Migrar gráficos oficiais 1:1 canônicos | F2 F3 |
| **F6** | Performance UI | Superfície do engine #10 | #10 F4 |
| **F7** | Rule Engine + Action Plan | Insights determinísticos + PAI | F2 |
| **F8** | IA Coordenadora | Briefs estruturados | F7 |
| **F9** | Sala de Situação | Composição única | F4 F7 F8 |
| **F10** | Ficha Clínica Estruturada | Campos controlados + LGPD | F1 F7 |
| **F11** | Simulador | Cenários rotulados | F2 F6 |
| **F12** | Consolidação | Observabilidade, paridade, desligar legado | E4 |

**Regra:** não iniciar superfície de UI de um módulo sem contrato de dados estável e testes anti-PII.

---

## 9. Backlog dividido por épicos

> Renomeação de produto: o “Epic 3” deste documento é a **visão BioMed Executive Intelligence**.  
> Os épicos técnicos abaixo reorganizam o backlog legado E1–E4 sem apagar o valor já construído em shadow.

### Épico A — Platform Foundation (seguro + canônico)

| ID | Item |
|----|------|
| A-01 | Gates PR #4 em qualquer HTTP novo |
| A-02 | API read-only de métricas canônicas (flag) |
| A-03 | API read-only de IQB (flag) |
| A-04 | Propagação de limitações/IQB nos contratos de UI |
| A-05 | Catálogo de feature flags + matriz de risco |

### Épico B — Design System & Shell

| ID | Item |
|----|------|
| B-01 | Tokens (cor, tipo, espaço) |
| B-02 | App shell + navegação IA (§4) |
| B-03 | KPI card + alert strip + empty states |
| B-04 | Chart frame padrão |
| B-05 | Piloto visual (Home ou Ingestão) |

### Épico C — Executive Surfaces

| ID | Item |
|----|------|
| C-01 | Home Command Center (8 cards) |
| C-02 | Índice Geral de Saúde Corporativa (definição + fórmula versionada) |
| C-03 | Risco Atual + Tendência (contratos) |
| C-04 | Performance BioMed surface |
| C-05 | Sala de Situação v1 |

### Épico D — Analytics Center

| ID | Item |
|----|------|
| D-01 | Inventário de gráficos legado → canônico |
| D-02 | Heatmap / Timeline / Pareto / Treemap |
| D-03 | Radar / Benchmark / Distribuições |
| D-04 | Filtros inteligentes + comparativos |
| D-05 | Sazonalidade / severidade / recorrência |
| D-06 | Desligar recálculo no frontend |

### Épico E — Action & Conditionants

| ID | Item |
|----|------|
| E-01 | Modelo de ação + status machine |
| E-02 | CRUD + histórico + revisão |
| E-03 | Ligação insight→ação |
| E-04 | Barreiras / decisão empresarial |
| E-05 | Resultado observado vs impacto esperado |

### Épico F — Intelligence & AI

| ID | Item |
|----|------|
| F-01 | Catálogo ≥30 regras determinísticas |
| F-02 | Avaliador + payload seguro |
| F-03 | Templates de insight |
| F-04 | AI Coordinator (schema + guards) |
| F-05 | Brief diário persistido |
| F-06 | Fallback determinístico sem LLM |

### Épico G — Clinical Card & Simulator

| ID | Item |
|----|------|
| G-01 | Schema Ficha Clínica Estruturada (sem anexos/exames) |
| G-02 | Controles de perfil/LGPD |
| G-03 | Simulador de cenários + rótulo HIPOTÉTICO |
| G-04 | ROI simulado separado de ROI observado |

### Épico H — Hardening corporativo

| ID | Item |
|----|------|
| H-01 | Observabilidade / audit log |
| H-02 | Backup/restore drills |
| H-03 | CI de contratos + anti-PII |
| H-04 | Rollout/rollback runbooks |
| H-05 | Remoção controlada do dashboard legado |

---

## 10. Dependências

```text
PR #4 (auth/tenant) ─────────────► qualquer HTTP / UI autenticada
PR #5 (métricas) ───────────────► Analytics, Home, Engine, Regras, IA, Simulador
PR #6 (IQB) ────────────────────► Home, Analytics warnings, Engine confiança, IA
PR #8 (ingestão) ───────────────► qualidade de entrada (não bloqueia UI read de histórico)
PR #10 (performance) ───────────► Performance UI, Home (Performance/ROI), Sala
Design System (B) ──────────────► todas as superfícies
Rule Engine (F) ────────────────► Action Plan, IA, Sala
Action Plan (E) ────────────────► Home (plano prioritário), Sala
IA (F) ─────────────────────────► Home (alertas/brief), Sala (faixa IA)
Ficha Clínica (G) ──────────────► Action Plan (apoio), nunca Analytics agregado
```

**Dependência externa de negócio:** headcount e custos explícitos para taxas populacionais e ROI observado — não inventar.

---

## 11. Estimativa de esforço

Sem datas de calendário. Esforço relativo por **invasividade e superfície**:

| Bloco | Complexidade | Componentes principais | Risco técnico |
|-------|--------------|------------------------|---------------|
| A Fundação segura + APIs read | **M** | auth gates, routers, contratos | Médio (segurança) |
| B Design system + shell | **M** | tokens, componentes, nav | Baixo–médio |
| C Home + Índice + Risco | **M** | agregação de cards, fórmulas novas versionadas | Médio (definição de índice) |
| D Analytics Center | **XL** | muitos gráficos, paridade, matar JS legado | Alto (regressão visual/dados) |
| E Action Plan | **L** | estado, histórico, permissões | Médio |
| F Rules + AI | **L–XL** | regras + schema IA + guards | Alto (alucinação/PII) |
| Performance UI | **M** | principalmente apresentação do #10 | Médio |
| Sala de Situação | **L** | composição + dados em tempo quase real | Médio |
| Ficha Clínica | **M–L** | LGPD, perfil, schema rígido | Alto (compliance) |
| Simulador | **M** | cenários + rótulos | Médio (confundir com observado) |
| Hardening H | **L** | ops, CI, runbooks | Médio |

**Ordem de valor para decisão executiva:** A → B → C → E/F → D → Sala → Simulador → Ficha (restrita) → H.

---

## 12. Critérios de aceite (globais e por módulo)

### 12.1 Globais

- [ ] Nenhuma métrica oficial calculada no frontend  
- [ ] Todo endpoint novo com `client_id` + auth (PR #4)  
- [ ] Saídas engine/IA passam guard anti-PII (testes)  
- [ ] Hipóteses rotuladas; causalidade não afirmada  
- [ ] ROI sem custos → `ROI_NAO_CALCULAVEL`  
- [ ] Flags default `false`  
- [ ] Documentação de fórmula/versão por indicador novo  
- [ ] Sem migration destrutiva; backup antes de qualquer mudança de schema autorizada  
- [ ] Paridade tenant: client 2 ⟂ client 4  

### 12.2 Por módulo (resumo)

| Módulo | Aceite-chave |
|--------|--------------|
| Home | ≤8 blocos decisórios; zero gráfico grande |
| Analytics | 100% gráficos oficiais via canônico; IQB visível |
| IA | Sem chat; schema validado; sem números novos |
| Action | Status machine + histórico + validação humana |
| Performance | Dimensões auditáveis; sem nota neutra falsa |
| Sala | Uma tela; sem poluição; deep-links com contexto |
| Ficha | Só entrevista estruturada; zero exames/anexos |
| Simulador | Rótulo HIPOTÉTICO; separado de ROI observado |
| UX | Tokens versionados; estados vazios/loading/erro |
| Arch | Diagrama + flags + runbooks atualizados |

---

## 13. Riscos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Big-bang de UI | Quebra operação da funcionária | Flags + migração gráfico a gráfico |
| IA inventar números | Decisão errada / LGPD | Schema + proibição + testes |
| Confundir simulado com observado | ROI falso | Rótulos + módulos separados |
| Ficha virar “prontuário” | Compliance | Schema fechado; sem anexos; papéis |
| Dashboard legado recalculando | Divergência canônica | Desligar JS de KPI |
| Headcount/custos ausentes | Taxas/ROI vazios | Limitações explícitas (já no engine) |
| Sobrecarga cognitiva | Home poluída | Orçamento rígido de 8 cards |
| Dependência de PRs shadow não mergeados | Atraso | Integrar por fatias com aceite |
| SQLite sob carga analítica | Lentidão | Agregados/cache futuro; sem full-scan UI |
| Escopo Epic 3 inchado | Não entrega | Fases F0–F12 com paradas |

---

## 14. Estratégia de rollout

1. **Shadow técnico** — serviços sem UI (já em curso: #5 #6 #8 #10).  
2. **UI flag off em staging/cópia** — Home e 1 gráfico piloto.  
3. **Canary interno BioMed** — um perfil admin, um tenant.  
4. **Pilot tenant** — CONVERPLAST ou RODA DE OURO (nunca ambos no primeiro dia).  
5. **Expand** — segundo tenant; Analytics gradual.  
6. **Default on** — só após aceite + treinamento + paridade.  
7. **Legacy off** — remover rotas/JS antigos em PR dedicado.

Cada passo: backup validado · flag · monitoramento · critério de abort (§15).

---

## 15. Estratégia de rollback

| Camada | Rollback |
|--------|----------|
| Feature flag | Desligar flag → UI/API nova some; legado permanece |
| Deploy app | Reverter release / unit file; **não** tocar DB |
| Schema (se houver, futuro) | Migração expansiva only; rollback de código compatível com colunas novas |
| Briefs IA | Desligar AIC; manter regras determinísticas |
| Action Plan v2 | Flag off; dados novos read-only preservados |
| Dados | Restaurar backup validado **somente** com autorização explícita |

**Nunca** rollback via “corrigir dados na mão” em produção sem protocolo.

Detalhe operacional complementar: alinhar a `ABSENTEISMO_ROLLBACK_STRATEGY.md` (branches de master docs).

---

## 16. Checklist final (gate de arquitetura)

### 16.1 Escopo documental

- [x] Arquitetura completa (§1)  
- [x] Mapa de módulos (§2)  
- [x] Fluxo completo (§3)  
- [x] Mapa de navegação (§4)  
- [x] Design System (§5)  
- [x] Arquitetura UX (§6)  
- [x] Arquitetura IA (§7)  
- [x] Roadmap (§8)  
- [x] Backlog por épicos (§9)  
- [x] Dependências (§10)  
- [x] Estimativa de esforço (§11)  
- [x] Critérios de aceite (§12)  
- [x] Riscos (§13)  
- [x] Rollout (§14)  
- [x] Rollback (§15)  

### 16.2 Proibições respeitadas nesta etapa

- [x] Não implementar código  
- [x] Não alterar banco / migrations / APIs  
- [x] Não alterar frontend / backend  
- [x] Não criar commit / PR / branch  
- [x] Não merge / deploy  

### 16.3 Alinhamento com legado documental

- Reutiliza camadas RAW/STANDARDIZED/CURATED do Target Architecture.  
- Estende (não apaga) a visão anterior de “Épico 3 — Biomed Insight” para a plataforma **Executive Intelligence**.  
- UX coerente com o adendo de modernização do Épico 2.  
- Performance/ROI/IQB coerentes com contratos do PR #10 e analytics A01/A02.

---

## Apêndice A — Índice Geral de Saúde Corporativa (definição a fechar)

Proposta de composição (versão `IGSC-v0`, **não implementar agora**):

| Componente | Fonte | Peso inicial (exemplo) |
|------------|-------|-------------------------|
| Tendência de absenteísmo (agregado) | canônico + engine | 25 |
| Severidade / duração | canônico | 20 |
| IQB | DQ | 15 |
| Performance BioMed | engine | 20 |
| Execução do plano | Action | 10 |
| Risco (alertas abertos) | regras | 10 |

Pesos efetivos redistribuídos quando dimensão `nao_avaliada` (mesmo padrão do score executivo do PR #10).  
Cobertura insuficiente → índice `INSUFICIENTE` / `None`, nunca “50 neutro”.

---

## Apêndice B — Glossário rápido

| Termo | Significado |
|-------|-------------|
| Fato | Dado agregado calculado por serviço versionado |
| Interpretação | Leitura cuidadosa sem causalidade |
| Hipótese | Afirmação incerta, explícita, com base |
| ROI observado | Exige premissas e coberturas equivalentes |
| ROI simulado | Apenas no Simulador, rótulo HIPOTÉTICO |
| Ficha Clínica Estruturada | Entrevista tipada; **não** prontuário |

---

## Apêndice C — Próximo passo recomendado (ainda sem código)

1. Revisar e aprovar este documento com stakeholders BioMed.  
2. Congelar IGSC-v0 e lista P0 da Home.  
3. Priorizar Épico A+B (fundação + shell) antes de qualquer tela nova.  
4. Só então abrir branch/PR de implementação — **fora deste documento**.

---

**Fim do documento de arquitetura.**  
Nenhuma implementação foi realizada.
