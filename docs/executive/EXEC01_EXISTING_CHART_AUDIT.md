# EXEC-01 — Auditoria de gráficos existentes

| Campo | Valor |
|-------|--------|
| **Documento** | `docs/executive/EXEC01_EXISTING_CHART_AUDIT.md` |
| **Repo** | AbsenteismoController |
| **Baseline auditado** | `540cda0` (Merge PR #11: Foundation Train FIT-01→FIT-07) |
| **Branch de destino da iniciativa** | `feat/executive-intelligence-redesign` (a criar a partir deste HEAD) |
| **Escopo de busca** | `frontend/*.html`, `frontend/static/js/*.js`, `backend/main.py` (+ `backend/analytics.py` para fórmulas) |
| **Stack encontrada** | Chart.js 3.9.1 / 4.4.0; canvas HTML; heatmap HTML/CSS (não Plotly); UI estilo Power BI (não embed real) |
| **Não encontrado** | Plotly, Power BI embed SDK, D3 standalone |
| **Data da auditoria** | 2026-08-07 |
| **Regra** | Somente documentação; nenhum código funcional alterado |

---

## 1. Resumo executivo

O produto concentra a maior parte das visualizações no **Dashboard** (`/` → `index.html` + `dashboard.js` + `GET /api/dashboard`), com espelhamento quase completo na **Apresentação** (`/apresentacao` → `GET /api/apresentacao`). Há superfícies paralelas de baixa qualidade (**Dashboard PowerBI** quebrado/simulado; **Dados PowerBI** recalcula no cliente a partir de dump completo) e páginas stub (**Análises**, **Tendências**) sem gráficos.

**Contagem de visualizações inventariadas:** **74** (IDs A01–K02; slides tipados da Apresentação contados 1:1)  

### Contagem por decisão

| Decisão | Qtd | Significado |
|----------|-----|-------------|
| **MANTER** | 9 | Valor claro; metodologia aceitável para o estágio atual |
| **MELHORAR** | 16 | Manter conceito; corrigir fórmula, naming, taxa/efetivo, UX ou qualidade |
| **CONSOLIDAR** | 35 | Redundante entre telas/clientes; unificar pipeline ou superfície |
| **SUBSTITUIR** | 6 | Formato ou pergunta analítica inadequada; trocar por outro tipo |
| **REMOVER** | 8 | Quebrado, simulado, stub vazio, risco ético/LGPD sem valor proporcional |

---

## 2. Convenções e achados transversais

### 2.1 Escopo por cliente no Dashboard

| Bloco DOM | Visibilidade (JS) | Observação |
|-----------|-------------------|------------|
| `#graficosConverplast` | `client_id === 2` | Comentário HTML “APENAS CONVERPLAST”; charts ainda são *renderizados* para outros clientes, mas o bloco fica `display:none` |
| `#graficosComparativos` | Todos | Comparativos mês/trimestre/ano + heatmap |
| `#graficosRodaOuro` | `client_id === 4` | 6 rankings + 6 horas perdidas |

### 2.2 Fontes canônicas vs paralelas

| Fonte | Uso |
|-------|-----|
| `GET /api/dashboard` | Fonte principal de séries do Dashboard |
| `GET /api/apresentacao` | Quase o mesmo cálculo + slides + textos IA |
| `GET /api/relatorios/comparativo` | Página Comparativos (períodos livres) |
| `GET /api/funcionario/perfil` | Perfil individual |
| `GET /api/dados/todos` | Dump completo → agregação no browser (Dados/Dashboard PowerBI) |
| `GET /api/produtividade` + `/api/produtividade/evolucao` | Produtividade assistencial (desacoplada de atestados) |
| `GET /api/clientes/{id}/graficos*` | **Stub** — endpoints removidos/vazios |
| `GET /api/analises/*`, `GET /api/tendencias` | APIs sem UI de gráfico (páginas stub) |

### 2.3 Riscos metodológicos recorrentes

1. **Absolutos sem efetivo** — setores/CID/heatmap comparam volume, não taxa por trabalhador.  
2. **Horas × dias** — conversão ad-hoc `horas/8` no frontend; KPI de horas sem fallback unificado.  
3. **“Taxa” mal nomeada** — em Comparativos, `variacoes.taxa` é variação de contagem de atestados, não absenteísmo.  
4. **Reupload / multi-mês** — evolução mensal sensível a uploads duplicados.  
5. **PII nominal** — top funcionários e rankings RO por nome.  
6. **Duplicação Dashboard ↔ Apresentação ↔ Comparativos ↔ PowerBI**.  
7. **Campos errados no PowerBI JS** — `dias_atestado` / `horas_atestado` vs modelo `dias_atestados` / `horas_perdi`.

### 2.4 Escala de qualidade metodológica

| Nível | Critério |
|-------|----------|
| **high** | Fórmula clara no backend; dimensão coerente; pouco risco de leitura invertida |
| **medium** | Útil, mas falta denominador, naming, ou há redundância/ambiguidade |
| **low** | Simulado, campo errado, stub, ou interpretação enganosa alta |

---

## 3. Inventário detalhado

Legenda de **decisão:** `MANTER` | `MELHORAR` | `CONSOLIDAR` | `SUBSTITUIR` | `REMOVER`

---

### A. Dashboard principal — KPIs

#### A01. KPI Dias Perdidos
| Campo | Valor |
|-------|--------|
| **name** | Dias Perdidos (card) |
| **screen/route** | `/` (Dashboard) |
| **source file** | `frontend/index.html` (`#cardDiasPerdidos`); `frontend/static/js/dashboard.js` → `renderizarCards` |
| **API endpoint(s)** | `GET /api/dashboard` → `metricas.total_dias_perdidos` |
| **formula/metrics** | `SUM(atestado.dias_atestados)` filtrado por `client_id`, mês, setor, funcionário (`Analytics.metricas_gerais`) |
| **dimension** | Empresa / período (escalar) |
| **purpose** | Impacto absoluto de afastamento em dias |
| **audience** | Gestores RH / SESMT / diretoria |
| **redundancy** | Espelhado em slides KPI da Apresentação; parcial com cards Comparativos |
| **methodological quality** | high |
| **interpretation risk** | Médio se período incompleto ou reupload inflar soma |
| **decision** | **MANTER** |
| **justification** | Métrica central do produto; base para o Command Center |

#### A02. KPI Horas Perdidas
| Campo | Valor |
|-------|--------|
| **name** | Horas Perdidas (card) |
| **screen/route** | `/` |
| **source file** | `frontend/index.html`; `dashboard.js` |
| **API endpoint(s)** | `GET /api/dashboard` → `metricas.total_horas_perdidas` |
| **formula/metrics** | `SUM(atestado.horas_perdi)` |
| **dimension** | Empresa / período |
| **purpose** | Impacto em jornada (atestados em horas) |
| **audience** | RH / operação |
| **redundancy** | Sobreposição conceitual com dias; RO tem bloco próprio de horas |
| **methodological quality** | medium |
| **interpretation risk** | Alto se horas nulas/imputadas e usuário comparar com dias sem regra clara |
| **decision** | **MELHORAR** |
| **justification** | Unificar regra de imputação/fallback e exibir unidade + cobertura de preenchimento |

---

### B. Dashboard — bloco Converplast (`#graficosConverplast`, UI só `client_id=2`)

#### B01. TOP 10 Doenças mais Frequentes
| Campo | Valor |
|-------|--------|
| **name** | TOP 10 Doenças (CID/diagnóstico) |
| **screen/route** | `/` |
| **source file** | `index.html` `#chartCids`; `dashboard.js` `renderizarChartCids` |
| **API endpoint(s)** | `/api/dashboard` → `top_cids` |
| **formula/metrics** | Contagem de atestados agrupados por nome/diagnóstico (não por código CID); exclui CIDs genéricos Z00/Z52/Z76; ordena por `quantidade` |
| **dimension** | Doença (diagnóstico) |
| **purpose** | Principais causas de afastamento |
| **audience** | SESMT / medicina do trabalho |
| **redundancy** | Apresentação `top_cids`; PowerBI doenças; RO classificação doenças |
| **methodological quality** | medium |
| **interpretation risk** | Fragmentação de texto; volume ≠ gravidade; sem taxa |
| **decision** | **MELHORAR** |
| **justification** | Manter ranking; adicionar Pareto/% acumulado e n mínimo |

#### B02. Evolução Mensal — Últimos 12 Meses
| Campo | Valor |
|-------|--------|
| **name** | Evolução Mensal |
| **screen/route** | `/` |
| **source file** | `#chartEvolucao`; `renderizarChartEvolucao` |
| **API endpoint(s)** | `/api/dashboard` → `evolucao_mensal` |
| **formula/metrics** | Série mensal de dias (e relacionados) via `Analytics.evolucao_mensal` |
| **dimension** | Tempo (mês) |
| **purpose** | Tendência de absenteísmo |
| **audience** | Diretoria / RH |
| **redundancy** | Apresentação; Dados PowerBI tendência; Comparativos |
| **methodological quality** | medium |
| **interpretation risk** | Reuploads e meses incompletos distorcem tendência |
| **decision** | **MELHORAR** |
| **justification** | Essencial; precisa sinal de qualidade/mês incompleto e média móvel |

#### B03. TOP 5 Setores
| Campo | Valor |
|-------|--------|
| **name** | TOP 5 Setores |
| **screen/route** | `/` |
| **source file** | `#chartSetores`; `renderizarChartSetores` |
| **API endpoint(s)** | `/api/dashboard` → `top_setores` |
| **formula/metrics** | `COUNT(*)`, `SUM(dias)`, `SUM(horas)` por `setor`; top 5 por quantidade |
| **dimension** | Setor |
| **purpose** | Onde concentrar ações |
| **audience** | Gestores de área / RH |
| **redundancy** | Centro de custo; RO setores; PowerBI setores |
| **methodological quality** | medium |
| **interpretation risk** | Setores maiores sempre “piores” em absoluto |
| **decision** | **MELHORAR** |
| **justification** | Trocar foco para taxa/100 trabalhadores quando efetivo existir |

#### B04. Por Gênero
| Campo | Valor |
|-------|--------|
| **name** | Distribuição por Gênero |
| **screen/route** | `/` |
| **source file** | `#chartGenero`; `renderizarChartGenero` |
| **API endpoint(s)** | `/api/dashboard` → `distribuicao_genero` |
| **formula/metrics** | Contagem (e/ou dias) por gênero |
| **dimension** | Gênero |
| **purpose** | Perfil demográfico dos afastamentos |
| **audience** | SESMT / DEI / RH |
| **redundancy** | RO análises de gênero/horas |
| **methodological quality** | medium |
| **interpretation risk** | Sem denominador populacional por gênero |
| **decision** | **MANTER** |
| **justification** | Útil como breakdown; evoluir para taxa quando headcount existir |

#### B05. Dias por Doença (título atual)
| Campo | Valor |
|-------|--------|
| **name** | Dias por Doença (`chartMediaCid`) |
| **screen/route** | `/` |
| **source file** | `#chartMediaCid`; `renderizarChartMediaCid` |
| **API endpoint(s)** | `/api/dashboard` → **`top_cids`** (campo `dias_perdidos`) — **não** `media_cid` |
| **formula/metrics** | `SUM(dias_atestados)` por doença do top CIDs |
| **dimension** | Doença |
| **purpose** | Gravidade absoluta por doença |
| **audience** | SESMT |
| **redundancy** | Alta com B01 (mesma fonte) e B14 (média) |
| **methodological quality** | low |
| **interpretation risk** | Título “média” no ID vs subtítulo “total de dias”; confusão com B14 |
| **decision** | **CONSOLIDAR** |
| **justification** | Fundir com B01 (duas séries: eventos + dias) ou remover e manter só média/Pareto |

#### B06. Dias Perdidos por Funcionários (TOP 10)
| Campo | Valor |
|-------|--------|
| **name** | TOP 10 Funcionários — Dias |
| **screen/route** | `/` |
| **source file** | `#chartFuncionariosDias`; `renderizarChartFuncionariosDias` |
| **API endpoint(s)** | `/api/dashboard` → `top_funcionarios` |
| **formula/metrics** | `SUM(dias_atestados)` por `nomecompleto` |
| **dimension** | Pessoa (PII) |
| **purpose** | Identificar casos extremos |
| **audience** | RH operacional (não ideal para tela executiva) |
| **redundancy** | RO classificação funcionários; PowerBI funcionários; Perfil |
| **methodological quality** | low |
| **interpretation risk** | Estigma, LGPD, uso indevido em reunião executiva |
| **decision** | **SUBSTITUIR** |
| **justification** | Substituir por faixas anônimas / casos recorrentes agregados no Command Center |

#### B07. Evolução de Dias Perdidos por Setor
| Campo | Valor |
|-------|--------|
| **name** | Evolução por Setor |
| **screen/route** | `/` |
| **source file** | `#chartEvolucaoSetor`; `renderizarChartEvolucaoSetor` |
| **API endpoint(s)** | `/api/dashboard` → `evolucao_setor` |
| **formula/metrics** | Séries mensais de dias por principais setores (`evolucao_por_setor`) |
| **dimension** | Setor × Tempo |
| **purpose** | Tendência setorial |
| **audience** | Gestores / SESMT |
| **redundancy** | Heatmap (mesma dualidade tempo×setor) |
| **methodological quality** | medium |
| **interpretation risk** | Muitas séries → clutter; sem taxa |
| **decision** | **MELHORAR** |
| **justification** | Manter; limitar a top-N + toggle; alinhar com heatmap |

#### B08. Escalas (Horários) com mais Atestados
| Campo | Valor |
|-------|--------|
| **name** | TOP 10 Escalas |
| **screen/route** | `/` |
| **source file** | `#chartEscalas`; `renderizarChartEscalas` |
| **API endpoint(s)** | `/api/dashboard` → `top_escalas` |
| **formula/metrics** | Contagem/dias por escala/horário |
| **dimension** | Escala |
| **purpose** | Hipótese turno × absenteísmo |
| **audience** | Operação / SESMT |
| **redundancy** | Baixa (específico) |
| **methodological quality** | medium |
| **interpretation risk** | Escalas com mais headcount dominam |
| **decision** | **MANTER** |
| **justification** | Sinal operacional único; melhorar com taxa quando possível |

#### B09. Motivos de Incidência
| Campo | Valor |
|-------|--------|
| **name** | Motivos de Incidência |
| **screen/route** | `/` |
| **source file** | `#chartMotivos`; `renderizarChartMotivos` |
| **API endpoint(s)** | `/api/dashboard` → `top_motivos` |
| **formula/metrics** | Distribuição percentual por `motivo_atestado` |
| **dimension** | Motivo |
| **purpose** | Mix de motivos cadastrais |
| **audience** | RH |
| **redundancy** | Baixa |
| **methodological quality** | medium |
| **interpretation risk** | Qualidade do campo motivo; categorias residuais |
| **decision** | **MANTER** |
| **justification** | Útil para auditoria cadastral e mix |

#### B10. Dias Perdidos por Centro de Custo
| Campo | Valor |
|-------|--------|
| **name** | Centro de Custo (TOP 10 setores) |
| **screen/route** | `/` |
| **source file** | `#chartCentroCusto`; `renderizarChartCentroCusto` |
| **API endpoint(s)** | `/api/dashboard` → `dias_centro_custo` |
| **formula/metrics** | Dias (e horas no tooltip) por setor/CC |
| **dimension** | Setor / centro de custo |
| **purpose** | Impacto por unidade de custo |
| **audience** | Finanças / gestores |
| **redundancy** | **Alta** com B03 (mesma dimensão setor) |
| **methodological quality** | medium |
| **interpretation risk** | Usuário vê “dois top setores” diferentes (count vs dias) |
| **decision** | **CONSOLIDAR** |
| **justification** | Um só ranking de setor com dual eixo eventos/dias (ou taxa) |

#### B11. Distribuição de Dias por Atestado
| Campo | Valor |
|-------|--------|
| **name** | Histograma de duração |
| **screen/route** | `/` |
| **source file** | `#chartDistribuicaoDias`; `renderizarChartDistribuicaoDias` |
| **API endpoint(s)** | `/api/dashboard` → `distribuicao_dias` |
| **formula/metrics** | Frequência por faixas de `dias_atestados` |
| **dimension** | Duração do atestado |
| **purpose** | Perfil curto vs longo |
| **audience** | SESMT / RH |
| **redundancy** | Baixa |
| **methodological quality** | high |
| **interpretation risk** | Faixas fracionárias / bins ruins |
| **decision** | **MANTER** |
| **justification** | Boa pergunta analítica; alinhar bins canônicos |

#### B12. Média de Dias por CID
| Campo | Valor |
|-------|--------|
| **name** | Média de Dias por CID |
| **screen/route** | `/` |
| **source file** | `#chartMediaCidDias`; `renderizarChartMediaCidDias` |
| **API endpoint(s)** | `/api/dashboard` → `media_cid` |
| **formula/metrics** | `AVG(dias_atestados)` por CID (com count/total); `dias_atestados > 0` |
| **dimension** | CID |
| **purpose** | Gravidade média por diagnóstico |
| **audience** | Medicina do trabalho |
| **redundancy** | Parcial com B05 |
| **methodological quality** | medium |
| **interpretation risk** | Médias com n pequeno; outliers |
| **decision** | **MELHORAR** |
| **justification** | Exibir n e suprimir n&lt;5; ordenar com critério estável |

#### B13. Dias Perdidos por Setor e Gênero
| Campo | Valor |
|-------|--------|
| **name** | Setor × Gênero |
| **screen/route** | `/` |
| **source file** | `#chartSetorGenero`; `renderizarChartSetorGenero` |
| **API endpoint(s)** | `/api/dashboard` → `dias_setor_genero` |
| **formula/metrics** | Dias cruzados setor × gênero |
| **dimension** | Setor × Gênero |
| **purpose** | Comparativo demográfico por área |
| **audience** | SESMT / RH |
| **redundancy** | RO horas setor×gênero |
| **methodological quality** | medium |
| **interpretation risk** | Sem efetivo por célula |
| **decision** | **MANTER** |
| **justification** | Cruzamento útil; evoluir para taxa |

#### B14. Comparativo: Dias vs Horas Perdidas (por setor)
| Campo | Valor |
|-------|--------|
| **name** | Dias vs Horas (setor) |
| **screen/route** | `/` |
| **source file** | `#chartComparativoDiasHoras`; `renderizarChartComparativoDiasHoras` |
| **API endpoint(s)** | `/api/dashboard` → `comparativo_dias_horas` |
| **formula/metrics** | Backend: SUM dias e horas por setor; **frontend** plota horas como `horas/8` (dias equivalentes) |
| **dimension** | Setor |
| **purpose** | Comparar modalidades dia vs hora |
| **audience** | RH / analistas |
| **redundancy** | RO comparativo gênero; KPI horas |
| **methodological quality** | low |
| **interpretation risk** | Fator 8h arbitrários; eixos misturados |
| **decision** | **MELHORAR** |
| **justification** | Separar eixos/unidades; documentar conversão ou abandoná-la |

#### B15. Frequência de Atestados por Funcionário
| Campo | Valor |
|-------|--------|
| **name** | Frequência (buckets de atestados) |
| **screen/route** | `/` |
| **source file** | `#chartFrequenciaAtestados`; `renderizarChartFrequenciaAtestados` |
| **API endpoint(s)** | `/api/dashboard` → `frequencia_atestados` |
| **formula/metrics** | Histograma: quantos funcionários têm 1, 2, 3… atestados |
| **dimension** | Recorrência (pessoa agregada) |
| **purpose** | Concentração de repetidores |
| **audience** | RH / SESMT |
| **redundancy** | Baixa (conceito bom) |
| **methodological quality** | medium |
| **interpretation risk** | Não é “taxa de absenteísmo”; título pode induzir |
| **decision** | **MELHORAR** |
| **justification** | Renomear; adicionar recorrência 30/60/90d no redesign |

#### B16. Produtividade — Consultas por Categoria
| Campo | Valor |
|-------|--------|
| **name** | Produtividade por categoria |
| **screen/route** | `/` |
| **source file** | `#chartProdutividade`; `renderizarChartProdutividade` |
| **API endpoint(s)** | `/api/dashboard` → `produtividade` (tabela produtividade, não atestados) |
| **formula/metrics** | Categorias (consultas/exames/etc.) do último mês cadastrado; faltas recalculadas no JS em parte |
| **dimension** | Categoria assistencial |
| **purpose** | Desempenho BioMed (não absenteísmo) |
| **audience** | Operação BioMed / diretoria clínica |
| **redundancy** | Página `/produtividade` (tabelas); slides apresentação |
| **methodological quality** | medium |
| **interpretation risk** | Misturar absenteísmo e produtividade na mesma tela |
| **decision** | **CONSOLIDAR** |
| **justification** | Mover para módulo Performance no Executive Intelligence |

#### B17. Produtividade — Evolução Mensal
| Campo | Valor |
|-------|--------|
| **name** | Evolução mensal de consultas |
| **screen/route** | `/` |
| **source file** | `#chartProdutividadeEvolucao`; `carregarEvolucaoProdutividade` |
| **API endpoint(s)** | `GET /api/produtividade/evolucao?agrupar_por=mes` |
| **formula/metrics** | Total de consultas mês a mês |
| **dimension** | Tempo |
| **purpose** | Tendência assistencial |
| **audience** | Operação BioMed |
| **redundancy** | B18; página produtividade |
| **methodological quality** | medium |
| **interpretation risk** | Endpoint/auth/cobertura incompleta |
| **decision** | **CONSOLIDAR** |
| **justification** | Unificar com módulo de performance |

#### B18. Produtividade — Distribuição Anual por Categoria
| Campo | Valor |
|-------|--------|
| **name** | Stacked % mês × categoria |
| **screen/route** | `/` |
| **source file** | `#chartProdutividadeMensalCategoria` |
| **API endpoint(s)** | `/api/dashboard` → `produtividade` |
| **formula/metrics** | Barras empilhadas percentuais mês a mês |
| **dimension** | Tempo × Categoria |
| **purpose** | Mix temporal de categorias |
| **audience** | Operação BioMed |
| **redundancy** | B16/B17 |
| **methodological quality** | medium |
| **interpretation risk** | % esconde volume absoluto |
| **decision** | **CONSOLIDAR** |
| **justification** | Um painel de produtividade com toggle absoluto/% |

---

### C. Dashboard — Comparativos & Heatmap (todos os clientes)

#### C01. Comparativo Mensal
| Campo | Valor |
|-------|--------|
| **name** | Comparativo Mensal |
| **screen/route** | `/` |
| **source file** | `#chartComparativoMensal`; `renderizarChartComparativoMensal` |
| **API endpoint(s)** | `/api/dashboard` → `comparativo_periodos_mes` |
| **formula/metrics** | Último mês **com dados** vs mês anterior; Δ% dias/horas/registros (`comparativo_periodos('mes')`) |
| **dimension** | Tempo (par de meses) |
| **purpose** | Variação curto prazo |
| **audience** | Diretoria / RH |
| **redundancy** | Página `/comparativos`; slides apresentação |
| **methodological quality** | medium |
| **interpretation risk** | “Atual” ≠ calendário; confundir com taxa |
| **decision** | **CONSOLIDAR** |
| **justification** | Uma superfície canônica de comparação temporal |

#### C02. Comparativo Trimestral
| Campo | Valor |
|-------|--------|
| **name** | Comparativo Trimestral |
| **screen/route** | `/` |
| **source file** | `#chartComparativoTrimestral` |
| **API endpoint(s)** | `/api/dashboard` → `comparativo_periodos_trimestre` |
| **formula/metrics** | Trimestre atual vs anterior (`tipo_comparacao='trimestre'`) |
| **dimension** | Tempo (trimestre) |
| **purpose** | Variação médio prazo |
| **audience** | Diretoria |
| **redundancy** | C01; `/comparativos` |
| **methodological quality** | medium |
| **interpretation risk** | Mesmos de C01 |
| **decision** | **CONSOLIDAR** |
| **justification** | Mesmo componente com seletor de granularidade |

#### C03. Comparativo Ano Anterior
| Campo | Valor |
|-------|--------|
| **name** | Comparativo Ano Anterior |
| **screen/route** | `/` |
| **source file** | `#chartComparativoAnoAnterior` |
| **API endpoint(s)** | `/api/dashboard` → `comparativo_ano_anterior` |
| **formula/metrics** | Ano atual vs mesmo período do ano anterior (série/pares) |
| **dimension** | Tempo (YoY) |
| **purpose** | Sazonalidade anual |
| **audience** | Diretoria |
| **redundancy** | `/comparativos` anual |
| **methodological quality** | medium |
| **interpretation risk** | Base YoY incompleta |
| **decision** | **MELHORAR** |
| **justification** | Manter YoY no redesign com denominador e flags de cobertura |

#### C04. Mapa de Calor — Setores × Meses
| Campo | Valor |
|-------|--------|
| **name** | Heatmap dias perdidos |
| **screen/route** | `/` |
| **source file** | `#chartHeatmap` (div HTML, não Chart.js); `renderizarChartHeatmap` / `renderizarHeatmapTabela` |
| **API endpoint(s)** | `/api/dashboard` → `heatmap_setores_meses` |
| **formula/metrics** | Matriz `SUM(dias_atestados)` por setor × `mes_referencia` |
| **dimension** | Setor × Tempo |
| **purpose** | Hotspots espaço-tempo |
| **audience** | SESMT / gestores |
| **redundancy** | B07 evolução setor; apresentação heatmap |
| **methodological quality** | medium |
| **interpretation risk** | Sem efetivo; setores grandes dominam cor |
| **decision** | **MELHORAR** |
| **justification** | Peça forte do produto; migrar para taxa e n por célula |

---

### D. Dashboard — Roda de Ouro (`client_id=4`)

#### D01. Classificação por Funcionário
| Campo | Valor |
|-------|--------|
| **name** | Classificação Funcionários RO |
| **screen/route** | `/` (seção RO) |
| **source file** | `#chartClassificacaoFuncionariosRO` |
| **API endpoint(s)** | `/api/dashboard` → `classificacao_funcionarios_ro` |
| **formula/metrics** | `SUM(dias_atestados)` por nome (campo `quantidade` = dias) |
| **dimension** | Pessoa |
| **purpose** | Ranking RO de afastamento |
| **audience** | Cliente RO / analistas |
| **redundancy** | B06 |
| **methodological quality** | low |
| **interpretation risk** | PII + naming `quantidade` enganoso |
| **decision** | **SUBSTITUIR** |
| **justification** | Mesma decisão de B06; versão cliente-específica não justifica PII em gráfico |

#### D02. Classificação Por Setor
| Campo | Valor |
|-------|--------|
| **name** | Classificação Setores RO |
| **screen/route** | `/` |
| **source file** | `#chartClassificacaoSetoresRO` |
| **API endpoint(s)** | `classificacao_setores_ro` |
| **formula/metrics** | `SUM(dias)` por setor (top 15) |
| **dimension** | Setor |
| **purpose** | Ranking setorial RO |
| **audience** | RO |
| **redundancy** | B03/B10 |
| **methodological quality** | medium |
| **interpretation risk** | Absolutos |
| **decision** | **CONSOLIDAR** |
| **justification** | Unificar ranking setorial multi-cliente |

#### D03. Dias atestados por Ano (Coerência)
| Campo | Valor |
|-------|--------|
| **name** | Dias/Ano — Coerente vs Sem Coerência |
| **screen/route** | `/` |
| **source file** | `#chartDiasAnoCoerencia` |
| **API endpoint(s)** | `dias_ano_coerencia` |
| **formula/metrics** | Dias agregados por ano × flag de coerência (regra RO) |
| **dimension** | Ano × Coerência |
| **purpose** | Qualidade/coerência de atestados RO |
| **audience** | Analistas RO |
| **redundancy** | D05 |
| **methodological quality** | medium |
| **interpretation risk** | Definição de “coerência” opaca ao executivo |
| **decision** | **MELHORAR** |
| **justification** | Manter conceito; documentar regra e integrar a IQB |

#### D04. Classificação por Doença
| Campo | Valor |
|-------|--------|
| **name** | Doenças × Dias RO |
| **screen/route** | `/` |
| **source file** | `#chartClassificacaoDoencasRO` |
| **API endpoint(s)** | `classificacao_doencas_ro` |
| **formula/metrics** | Ranking doença × dias |
| **dimension** | Doença |
| **purpose** | Causas RO |
| **audience** | SESMT RO |
| **redundancy** | B01/B05 |
| **methodological quality** | medium |
| **interpretation risk** | Fragmentação textual |
| **decision** | **CONSOLIDAR** |
| **justification** | Mesmo gráfico de doenças canônico |

#### D05. Análise Atestados (coerência %)
| Campo | Valor |
|-------|--------|
| **name** | Percentual de coerência |
| **screen/route** | `/` |
| **source file** | `#chartAnaliseCoerencia` |
| **API endpoint(s)** | `analise_coerencia` |
| **formula/metrics** | % coerente vs não |
| **dimension** | Coerência |
| **purpose** | KPI de qualidade documental |
| **audience** | RO / qualidade |
| **redundancy** | D03 |
| **methodological quality** | medium |
| **interpretation risk** | Pizza/% sem n |
| **decision** | **MELHORAR** |
| **justification** | Exibir n; alinhar com Data Quality (IQB) |

#### D06. Tempo Serviço × Atestados
| Campo | Valor |
|-------|--------|
| **name** | Tempo de serviço × atestados |
| **screen/route** | `/` |
| **source file** | `#chartTempoServicoAtestados` |
| **API endpoint(s)** | `tempo_servico_atestados` |
| **formula/metrics** | Atestados (ou dias) por faixa de tempo de casa |
| **dimension** | Tenure |
| **purpose** | Hipótese tenure × absenteísmo |
| **audience** | RH RO |
| **redundancy** | PowerBI tempo serviço (**simulado**) |
| **methodological quality** | medium |
| **interpretation risk** | Faixas e qualidade do campo admissão |
| **decision** | **MELHORAR** |
| **justification** | Conceito bom; validar fonte de tenure |

#### D07. Horas Perdidas por Gênero
| Campo | Valor |
|-------|--------|
| **name** | Horas × Gênero (44h=1 semana) |
| **screen/route** | `/` |
| **source file** | `#chartHorasPerdidasGenero` |
| **API endpoint(s)** | `horas_perdidas_genero` |
| **formula/metrics** | `SUM(horas_perdi)` por gênero; UI referencia 44h/semana |
| **dimension** | Gênero |
| **purpose** | Impacto jornada por gênero |
| **audience** | RO |
| **redundancy** | B04; D10–D12 |
| **methodological quality** | medium |
| **interpretation risk** | Conversão 44h; sem efetivo |
| **decision** | **MELHORAR** |
| **justification** | Padronizar unidade (horas vs semanas) |

#### D08. TOP 10 Setores — Horas Perdidas
| Campo | Valor |
|-------|--------|
| **name** | Setores por horas |
| **screen/route** | `/` |
| **source file** | `#chartHorasPerdidasSetor` |
| **API endpoint(s)** | `horas_perdidas_setor` |
| **formula/metrics** | Top 10 `SUM(horas)` por setor |
| **dimension** | Setor |
| **purpose** | Hotspots de horas |
| **audience** | RO |
| **redundancy** | B03/B10/D02 |
| **methodological quality** | medium |
| **interpretation risk** | Absolutos |
| **decision** | **CONSOLIDAR** |
| **justification** | Um ranking setorial com toggle dias/horas/taxa |

#### D09. Evolução Mensal de Horas Perdidas
| Campo | Valor |
|-------|--------|
| **name** | Evolução horas |
| **screen/route** | `/` |
| **source file** | `#chartEvolucaoMensalHoras` |
| **API endpoint(s)** | `evolucao_mensal_horas` |
| **formula/metrics** | Série mensal de horas |
| **dimension** | Tempo |
| **purpose** | Tendência de horas |
| **audience** | RO |
| **redundancy** | B02 |
| **methodological quality** | medium |
| **interpretation risk** | Paridade com evolução de dias |
| **decision** | **CONSOLIDAR** |
| **justification** | Dual-axis ou toggle na evolução canônica |

#### D10. Comparativo Dias vs Horas vs Semanas (gênero)
| Campo | Valor |
|-------|--------|
| **name** | Dias/Horas/Semanas × Gênero |
| **screen/route** | `/` |
| **source file** | `#chartComparativoDiasHorasGenero` |
| **API endpoint(s)** | `comparativo_dias_horas_genero` |
| **formula/metrics** | Métricas cruzadas; semanas derivadas (ex. horas/44) |
| **dimension** | Gênero × unidade |
| **purpose** | Multi-unidade por gênero |
| **audience** | RO |
| **redundancy** | B14; D07; D12 |
| **methodological quality** | low |
| **interpretation risk** | Três unidades no mesmo gráfico |
| **decision** | **SUBSTITUIR** |
| **justification** | Substituir por seletor de unidade + um comparativo limpo |

#### D11. Horas Perdidas por Setor e Gênero
| Campo | Valor |
|-------|--------|
| **name** | Setor × Gênero (horas) |
| **screen/route** | `/` |
| **source file** | `#chartHorasPerdidasSetorGenero` |
| **API endpoint(s)** | `horas_perdidas_setor_genero` |
| **formula/metrics** | Cruzamento horas |
| **dimension** | Setor × Gênero |
| **purpose** | Detalhe RO |
| **audience** | RO |
| **redundancy** | B13 |
| **methodological quality** | medium |
| **interpretation risk** | Absolutos |
| **decision** | **CONSOLIDAR** |
| **justification** | Mesmo cruzamento com toggle dias/horas |

#### D12. Análise Detalhada por Gênero
| Campo | Valor |
|-------|--------|
| **name** | % dias/horas/registros por gênero |
| **screen/route** | `/` |
| **source file** | `#chartAnaliseDetalhadaGenero` |
| **API endpoint(s)** | `analise_detalhada_genero` |
| **formula/metrics** | Percentuais múltiplos por gênero |
| **dimension** | Gênero |
| **purpose** | Visão composta |
| **audience** | RO |
| **redundancy** | D07/D10/B04 |
| **methodological quality** | low |
| **interpretation risk** | Muitas % sem base |
| **decision** | **CONSOLIDAR** |
| **justification** | Absorver em breakdown demográfico único |

---

### E. Dashboard — stubs / personalizados

#### E01. Gráficos personalizados (API removida)
| Campo | Valor |
|-------|--------|
| **name** | Gráficos configuráveis por cliente |
| **screen/route** | `/` (código residual em `dashboard.js`) |
| **source file** | `dashboard.js` `renderizarGraficoPersonalizado`; `main.py` `/api/clientes/{id}/graficos*` |
| **API endpoint(s)** | `GET/PUT /api/clientes/{id}/graficos` (retorna vazio); `POST .../gerar-dados` (“Endpoint removido”) |
| **formula/metrics** | N/A |
| **dimension** | N/A |
| **purpose** | Legado de customização |
| **audience** | Ninguém (morto) |
| **redundancy** | — |
| **methodological quality** | low |
| **interpretation risk** | Confusão de manutenção |
| **decision** | **REMOVER** |
| **justification** | Código/API mortos; limpar no redesign |

---

### F. Apresentação executiva (`/apresentacao`)

Fonte: `frontend/apresentacao.html` + `frontend/static/js/apresentacao.js` + `GET /api/apresentacao`.  
Quase todos os slides com gráfico **espelham** seções B/C/D. Decisão padrão: **CONSOLIDAR** (uma engine de chart; apresentação consome o mesmo contrato).

| ID | name (slide tipo) | decision | quality | interpretation risk | justification |
|----|-------------------|----------|---------|---------------------|---------------|
| F01 | KPIs (slide) | CONSOLIDAR | high | baixo | Reusar A01/A02 |
| F02 | `funcionarios_dias` | SUBSTITUIR | low | PII em reunião | Igual B06 |
| F03 | `top_cids` | CONSOLIDAR | medium | volume≠gravidade | Igual B01 |
| F04 | `evolucao_mensal` | CONSOLIDAR | medium | reupload | Igual B02 |
| F05 | `top_setores` | CONSOLIDAR | medium | absoluto | Igual B03 |
| F06 | `genero` | CONSOLIDAR | medium | sem efetivo | Igual B04 |
| F07 | `dias_doenca` | CONSOLIDAR | low | naming | Igual B05 |
| F08 | `escalas` | CONSOLIDAR | medium | headcount | Igual B08 |
| F09 | `motivos` | CONSOLIDAR | medium | cadastro | Igual B09 |
| F10 | `centro_custo` | CONSOLIDAR | medium | vs top setores | Igual B10 |
| F11 | `distribuicao_dias` | CONSOLIDAR | high | bins | Igual B11 |
| F12 | `media_cid` | CONSOLIDAR | medium | n pequeno | Igual B12 |
| F13 | `setor_genero` | CONSOLIDAR | medium | absoluto | Igual B13 |
| F14 | `evolucao_setor` | CONSOLIDAR | medium | clutter | Igual B07 |
| F15 | `comparativo_mensal` | CONSOLIDAR | medium | “atual” | Igual C01 |
| F16 | `comparativo_trimestral` | CONSOLIDAR | medium | — | Igual C02 |
| F17 | `comparativo_ano_anterior` | CONSOLIDAR | medium | cobertura | Igual C03 |
| F18 | `heatmap` | CONSOLIDAR | medium | sem efetivo | Igual C04 |
| F19 | `comparativo_dias_horas` | CONSOLIDAR | low | /8 | Igual B14 |
| F20 | `frequencia_atestados` | CONSOLIDAR | medium | “taxa” | Igual B15 |
| F21 | `produtividade` (+ subcharts categoria/evolução) | CONSOLIDAR | medium | mistura temas | Igual B16–B18 |
| F22 | RO set (`classificacao_*`, coerência, tenure, horas*) | CONSOLIDAR / SUBSTITUIR (PII) | low–medium | PII / unidades | Igual D01–D12 |
| F23 | Slides de ações (texto, sem chart) | MANTER | high | baixo | Conteúdo narrativo; fora do escopo chart mas presente na deck |

**API:** `GET /api/apresentacao?client_id=…` (+ filtros).  
**Audience:** reuniões executivas / demos.  
**Purpose:** storytelling com insights IA (`insights_engine.gerar_analise_grafico`).  
**Redundancy:** **máxima** com Dashboard.

---

### G. Página Comparativos (`/comparativos`)

#### G01. Gráfico barras Período 1 vs Período 2
| Campo | Valor |
|-------|--------|
| **name** | Comparativo de períodos (barras agrupadas) |
| **screen/route** | `/comparativos` |
| **source file** | `frontend/comparativos.html` `#chartComparativo`; `frontend/static/js/comparativos.js` |
| **API endpoint(s)** | `GET /api/relatorios/comparativo` |
| **formula/metrics** | `metricas_gerais` em dois intervalos; Δ% atestados/dias/horas; **`taxa` = variação de total_atestados** (não absenteísmo) |
| **dimension** | Período (usuário define) |
| **purpose** | Comparação ad-hoc |
| **audience** | Analistas / gestores |
| **redundancy** | C01–C03 |
| **methodological quality** | low (label Taxa) / medium (ideia) |
| **interpretation risk** | Alto — “Taxa” engana |
| **decision** | **MELHORAR** |
| **justification** | Manter períodos livres; corrigir naming; unificar com engine de C01–C03 |

---

### H. Perfil do funcionário (`/perfil_funcionario`)

#### H01. Evolução mensal do indivíduo
| Campo | Valor |
|-------|--------|
| **name** | Evolução dias — pessoa |
| **screen/route** | `/perfil_funcionario?nome=…` |
| **source file** | `perfil_funcionario.html` `#chartEvolucao`; `perfil_funcionario.js` |
| **API endpoint(s)** | `GET /api/funcionario/perfil` |
| **formula/metrics** | Dias perdidos mês a mês da pessoa |
| **dimension** | Pessoa × Tempo |
| **purpose** | Case management |
| **audience** | RH operacional |
| **redundancy** | Baixa (nível pessoa) |
| **methodological quality** | medium |
| **interpretation risk** | PII; acesso indevido |
| **decision** | **MANTER** |
| **justification** | Útil operacionalmente; reforçar auth/auditoria |

#### H02. TOP 5 CIDs da pessoa
| Campo | Valor |
|-------|--------|
| **name** | TOP CIDs — pessoa |
| **screen/route** | `/perfil_funcionario` |
| **source file** | `#chartCids`; `renderizarGraficoCids` |
| **API endpoint(s)** | `/api/funcionario/perfil` → `top_cids` |
| **formula/metrics** | Contagem por CID do indivíduo |
| **dimension** | CID × Pessoa |
| **purpose** | Histórico diagnóstico |
| **audience** | RH / SESMT |
| **redundancy** | Baixa |
| **methodological quality** | medium |
| **interpretation risk** | Dados sensíveis de saúde |
| **decision** | **MANTER** |
| **justification** | Contexto clínico-ocupacional no perfil; controle de acesso |

---

### I. Dados PowerBI (`/dados_powerbi`)

#### I01. Tendência Mensal (ano)
| Campo | Valor |
|-------|--------|
| **name** | Tendência Mensal (registros/dias/horas) |
| **screen/route** | `/dados_powerbi` |
| **source file** | `dados_powerbi.html` `#chartTendenciaMensal`; `dados_powerbi.js` `criarGraficoTendenciaMensal` |
| **API endpoint(s)** | `GET /api/dados/todos` (dump) → agregação **no browser** |
| **formula/metrics** | Group-by mês no JS sobre todos os atestados |
| **dimension** | Tempo |
| **purpose** | Análise anual na grade de dados |
| **audience** | Analistas de dados |
| **redundancy** | B02 |
| **methodological quality** | low |
| **interpretation risk** | Full dump; 3 eixos Y; divergência do `/api/dashboard` |
| **decision** | **MELHORAR** |
| **justification** | Usar endpoint agregado server-side; alinhar a evolução canônica |

#### I02. Tendência Acumulada
| Campo | Valor |
|-------|--------|
| **name** | Acumulado dias/horas |
| **screen/route** | `/dados_powerbi` |
| **source file** | `#chartTendenciaAcumulado`; `criarGraficoAcumulado` |
| **API endpoint(s)** | mesmo dump `/api/dados/todos` |
| **formula/metrics** | Soma cumulativa mensal |
| **dimension** | Tempo |
| **purpose** | Visão YTD |
| **audience** | Analistas |
| **redundancy** | I01 / B02 |
| **methodological quality** | low |
| **interpretation risk** | Mesmos de I01 |
| **decision** | **CONSOLIDAR** |
| **justification** | Toggle acumulado na evolução canônica |

---

### J. Dashboard PowerBI (`/dashboard_powerbi`) — superfície quebrada

`DOMContentLoaded` chama `carregarResumo` / `carregarComparativos` / `carregarTendencias` **inexistentes**. `loadPowerbiData` / `createAllCharts` existem mas **não são invocados**. Charts usam campos `dias_atestado`/`horas_atestado` (incorretos) e dados **simulados**.

#### J01. Classificação por Funcionário (PowerBI)
| Campo | Valor |
|-------|--------|
| **name** | PowerBI — Funcionários |
| **screen/route** | `/dashboard_powerbi` |
| **source file** | `dashboard_powerbi.html` `#chartFuncionarios`; `dashboard_powerbi.js` |
| **API endpoint(s)** | Pretendido: `/api/dados/todos` (não ligado no init) |
| **formula/metrics** | Top 10 dias (campo errado) |
| **dimension** | Pessoa |
| **purpose** | Clone Power BI |
| **audience** | — |
| **redundancy** | B06/D01 |
| **methodological quality** | low |
| **interpretation risk** | Alto (quebrado + PII) |
| **decision** | **REMOVER** |
| **justification** | Página não inicializa; duplicata insegura |

#### J02–J07. Demais PowerBI (todos REMOVER)

| ID | name | Motivo |
|----|------|--------|
| J02 | Classificação por Setor | Duplicata de B03; init quebrado |
| J03 | Dias Atestados por Ano | Init quebrado; campo errado |
| J04 | Classificação por Doença | Duplicata; init quebrado |
| J05 | Análise Atestados (pie) | Valores **hardcoded** (45/12/8/5) — simulado |
| J06 | Tempo Serviço × Atestados | Faixas **hardcoded** — simulado |
| J07 | KPI Taxa de Absenteísmo | Fórmula inventada `(dias/(registros*30))*100` |

Detalhe J05/J06: comentários no código “*simulado*”; não refletem banco.

---

### K. Páginas e APIs órfãs (sem gráfico renderizado)

#### K01. Análises (`/analises`)
| Campo | Valor |
|-------|--------|
| **name** | Página Análises (stub) |
| **screen/route** | `/analises` |
| **source file** | `frontend/analises.html` (“em desenvolvimento”) |
| **API endpoint(s)** | Existem `GET /api/analises/funcionarios|setores|cids` sem UI |
| **formula/metrics** | N/A na UI |
| **dimension** | — |
| **purpose** | Placeholder |
| **audience** | — |
| **redundancy** | Dashboard |
| **methodological quality** | low |
| **interpretation risk** | Navegação morta |
| **decision** | **REMOVER** ou **SUBSTITUIR** pelo Command Center |
| **justification** | Substituir pela IA Executiva; remover stub |

*(Contado como **SUBSTITUIR** na consolidação de decisões.)*

#### K02. Tendências (`/tendencias`)
| Campo | Valor |
|-------|--------|
| **name** | Página Tendências (stub) |
| **screen/route** | `/tendencias` |
| **source file** | `frontend/tendencias.html` |
| **API endpoint(s)** | `GET /api/tendencias` (órfã da UI) |
| **decision** | **SUBSTITUIR** |
| **justification** | Virar módulo de tendência canônica do redesign |

---

### L. Superfícies sem Chart.js (contexto)

| ID | name | route | notes | decision |
|----|------|-------|-------|----------|
| L01 | Tabela produtividade | `/produtividade` | Inputs/consolidados; sem canvas | Fora do inventário chart; **MANTER** como captura operacional |
| L02 | Tabela INSS | `/inss` | Grid CID10; sem chart | N/A chart |
| L03 | Landing marketing | `/landing` | Texto menciona gráficos; sem chart real | N/A |
| L04 | Auto processor | `/auto_processor` | Carrega Chart.js CDN mas não instancia charts | **REMOVER** CDN morto (oportunidade cleanup) |

---

## 4. Matriz de decisão (IDs auditados)

| ID | Nome curto | Decisão |
|----|------------|----------|
| A01 | KPI Dias | MANTER |
| A02 | KPI Horas | MELHORAR |
| B01 | Top doenças | MELHORAR |
| B02 | Evolução mensal | MELHORAR |
| B03 | Top setores | MELHORAR |
| B04 | Gênero | MANTER |
| B05 | Dias por doença (misnamed) | CONSOLIDAR |
| B06 | Top funcionários | SUBSTITUIR |
| B07 | Evolução setor | MELHORAR |
| B08 | Escalas | MANTER |
| B09 | Motivos | MANTER |
| B10 | Centro de custo | CONSOLIDAR |
| B11 | Distribuição dias | MANTER |
| B12 | Média CID | MELHORAR |
| B13 | Setor×Gênero | MANTER |
| B14 | Dias vs Horas | MELHORAR |
| B15 | Frequência | MELHORAR |
| B16–B18 | Produtividade ×3 | CONSOLIDAR |
| C01–C02 | Comp. mês/trim | CONSOLIDAR |
| C03 | Comp. YoY | MELHORAR |
| C04 | Heatmap | MELHORAR |
| D01 | RO funcionários | SUBSTITUIR |
| D02 | RO setores | CONSOLIDAR |
| D03 | RO coerência ano | MELHORAR |
| D04 | RO doenças | CONSOLIDAR |
| D05 | RO % coerência | MELHORAR |
| D06 | RO tenure | MELHORAR |
| D07 | RO horas gênero | MELHORAR |
| D08–D09 | RO horas setor/evol | CONSOLIDAR |
| D10 | RO multi-unidade | SUBSTITUIR |
| D11–D12 | RO cruzamentos | CONSOLIDAR |
| E01 | Personalizados stub | REMOVER |
| F01–F22 | Slides chart | CONSOLIDAR / SUBSTITUIR (PII) |
| F23 | Slides ações | MANTER |
| G01 | Comparativos página | MELHORAR |
| H01–H02 | Perfil | MANTER |
| I01 | Tendência dados | MELHORAR |
| I02 | Acumulado dados | CONSOLIDAR |
| J01–J07 | Dashboard PowerBI | REMOVER |
| K01 | Análises stub | SUBSTITUIR |
| K02 | Tendências stub | SUBSTITUIR |

### Contagens finais (74 IDs)

| Decisão | Contagem | IDs |
|----------|----------|-----|
| **MANTER** | **9** | A01, B04, B08, B09, B11, B13, F23, H01, H02 |
| **MELHORAR** | **16** | A02, B01, B02, B03, B07, B12, B14, B15, C03, C04, D03, D05, D06, D07, G01, I01 |
| **CONSOLIDAR** | **35** | B05, B10, B16–B18, C01–C02, D02, D04, D08–D09, D11–D12, F01, F03–F22, I02 |
| **SUBSTITUIR** | **6** | B06, D01, D10, F02, K01, K02 |
| **REMOVER** | **8** | E01, J01–J07 |

**Canvas/DOM no frontend (referência):** ~33 no Dashboard (`index.html`) + heatmap div + 6 PowerBI + 2 Dados + 1 Comparativos + 2 Perfil ≈ **44** elementos de desenho; Apresentação reusa um `#chartSlide` dinâmico por tipo de slide (F*).

---

## 5. Prioridades sugeridas para `feat/executive-intelligence-redesign`

1. **REMOVER** Dashboard PowerBI e stubs de gráficos personalizados.  
2. **SUBSTITUIR** rankings nominais por agregados/anônimos no nível executivo.  
3. **CONSOLIDAR** Dashboard ↔ Apresentação ↔ Comparativos em uma *chart engine* + contratos canônicos (alinhar a MetricService shadow).  
4. **MELHORAR** setores/heatmap/evolução com denominador (efetivo), flags IQB e naming honesto de “taxa”.  
5. **MANTER** núcleo: dias perdidos, distribuição de duração, motivos, escalas, perfil operacional, narrativa de ações.

---

## 6. Referências de código (baseline `540cda0`)

| Área | Paths |
|------|--------|
| Dashboard UI | `frontend/index.html`, `frontend/static/js/dashboard.js` |
| Apresentação | `frontend/apresentacao.html`, `frontend/static/js/apresentacao.js` |
| Comparativos | `frontend/comparativos.html`, `frontend/static/js/comparativos.js` |
| Perfil | `frontend/perfil_funcionario.html`, `frontend/static/js/perfil_funcionario.js` |
| Dados / PowerBI | `frontend/dados_powerbi.html`, `dados_powerbi.js`, `dashboard_powerbi.html`, `dashboard_powerbi.js` |
| API | `backend/main.py` (`/api/dashboard`, `/api/apresentacao`, `/api/relatorios/comparativo`, `/api/dados/todos`, `/api/funcionario/perfil`, `/api/produtividade*`) |
| Fórmulas | `backend/analytics.py` |
| Inventário prévio (analítico) | `docs/auditoria_analitica/ABS_CHART_INVENTORY.md` |
| Arquitetura alvo | `docs/master/BIOMED_EXECUTIVE_INTELLIGENCE_ARCHITECTURE.md` |

---

*Fim EXEC-01.*
