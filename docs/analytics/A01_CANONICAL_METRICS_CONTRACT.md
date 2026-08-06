# A01-A — Contrato de Métricas Canônicas (modo conferência / shadow)

**Status:** shadow — não substitui dashboard, gráficos nem `analytics.py` em produção.  
**Branch de referência:** `feat/a01a-canonical-metrics-shadow`  
**Clientes reais de conferência (somente leitura / testes sintéticos):** CONVERPLAST `client_id=2`, RODA DE OURO `client_id=4`.  
**Serviço:** `backend/services/metric_service.py`  
**Comparação local:** `backend/services/shadow_compare.py`

---

## 1. Objetivo

Calcular métricas oficiais candidatas em uma camada isolada, permitindo comparação com os resultados atuais das telas **sem** alterar visualizações neste lote.

O serviço:

- recebe explicitamente `db`, `client_id`, período e filtros opcionais;
- **nunca** usa fallback `client_id=1`;
- **nunca** infere tenant pelo frontend;
- é independente de HTTP e reutilizável por endpoints futuros;
- **não** expõe nomes, CPF, matrícula ou dados clínicos individuais.

---

## 2. Escopo de dados

| Conceito | Fonte | Observação |
|----------|--------|------------|
| Tenant | `Upload.client_id` | Join `Atestado` → `Upload` |
| Período | `Upload.mes_referencia` (`YYYY-MM`) | Filtro inclusivo início/fim |
| Evento | linha `Atestado` | Sem deduplicação |
| Dias | `Atestado.dias_atestados` | Negativos/nulos tratados como 0 e registrados em qualidade |
| Horas registradas | `Atestado.horas_perdi` | Somente valores `> 0` |
| Horas estimadas | `dias_atestados * horas_dia` | Somente se `horas_perdi` ausente/≤0 e ambos válidos |
| Setor | `Atestado.setor` | Label `SEM_SETOR` se vazio |
| Centro de custo | `Atestado.centro_custo` | Label `SEM_CENTRO_CUSTO` se vazio — **não** sinônimo de setor |
| CID (grupo) | 1ª letra de `Atestado.cid` | Capítulos A–Z; `SEM_CID` / `OUTROS` |

---

## 3. Definição de cada métrica

| Métrica | Definição | Unidade | Arredondamento |
|---------|-----------|---------|----------------|
| `eventos` | Contagem de linhas `Atestado` no escopo | inteiro | — |
| `trabalhadores_unicos` | Cardinalidade do conjunto de chaves internas de trabalhador | inteiro | — |
| `dias_perdidos` | Soma de `dias_atestados` válidos (≥0) | dias | 4 casas |
| `horas_perdidas_registradas` | Soma de `horas_perdi` onde `> 0` | horas | 4 casas |
| `horas_perdidas_estimadas` | Soma de `dias * horas_dia` quando não há horas registradas | horas | 4 casas |
| `duracao_media_dias` | Média de `dias_atestados` nos eventos com dias `> 0` | dias | 4 casas; `null` se denominador 0 |
| `horas_media_evento` | Média de `horas_perdi` nos eventos com horas registradas `> 0` | horas | 4 casas; `null` se denominador 0 |
| `eventos_por_100_trabalhadores` | `100 * eventos / efetivo_trabalhadores` | taxa | 4 casas; só com headcount externo válido `> 0` |
| `dias_perdidos_por_trabalhador` | `dias_perdidos / trabalhadores_unicos` | dias/trab. | 4 casas; `null` se 0 trabalhadores |

**Não implementado neste lote:** taxa oficial de absenteísmo (exige denominador de horas previstas comprovado).

---

## 4. Identidade de trabalhador (uso interno)

Função: `worker_identity_key(atestado)`.

Prioridade atual (sem alterar banco):

1. `matricula` (trim, case-insensitive) → `mat:…`
2. senão `cpf` (somente dígitos) → `cpf:…`
3. senão `nomecompleto` / `nome_funcionario` normalizado → `nome:…`

**Limitação documentada:** o analytics legado usa `distinct(nomecompleto)`. Nomes iguais com matrículas diferentes (ou o inverso) geram divergências esperadas no modo shadow. Chaves **nunca** entram no JSON de saída.

Auditoria: hoje o sistema **não** possui identificador estável de trabalhador no schema; matrícula/CPF são opcionais e inconsistentes entre uploads.

---

## 5. Setor vs centro de custo

- Campos separados no modelo e no contrato (`distribuicao_setor`, `distribuicao_centro_custo`).
- **Não** há fallback de um para o outro neste serviço.
- Nota histórica: partes do analytics legado tratam/documentam CC≈setor — isso **não** é adotado aqui.

---

## 6. CID

- Agrupamento coletivo por **capítulo** (letra inicial), adequado à visão gerencial.
- Código CID completo: previsto apenas para contexto técnico autorizado futuro — **não** retornado por padrão.
- Flag `suppress_small_groups` / `small_group_threshold=5`: prepara supressão de grupos com menos de 5 trabalhadores (desligada por padrão).
- Ausência → bucket `SEM_CID`.
- Sem CID por pessoa, nomes ou registros identificáveis.

---

## 7. Registrado versus estimado (horas)

| Campo | Conteúdo |
|-------|----------|
| `horas_perdidas_registradas` | Somente `horas_perdi > 0` |
| `horas_perdidas_estimadas` | Somente estimativa `dias * horas_dia` |
| `qualidade.horas` | `registrada` \| `estimada` \| `mista` \| `indisponivel` |
| `metodologia.campo_horas` | `horas_perdi` |
| `metodologia.campo_horas_estimativa` | documenta a fórmula |

**Nunca** misturar registrado e estimado em um único campo numérico.

---

## 8. Qualidade e denominadores

| Campo | Valores |
|-------|---------|
| `qualidade.horas` | ver §7 |
| `qualidade.denominador_efetivo` | `valido` / `incompleto` / `indisponivel` |
| `qualidade.notas` | avisos (nulos, negativos, headcount ausente, etc.) |

`efetivo_trabalhadores` é **opcional e externo**. Sem ele, `eventos_por_100_trabalhadores` fica `null` e o denominador é `indisponivel`. Horas previstas oficiais **não** são usadas neste lote.

---

## 9. Filtros

Obrigatórios: `db`, `client_id` (>0).  
Opcionais: `periodo_inicio`, `periodo_fim`, `setor`, `centro_custo`, `efetivo_trabalhadores`, `suppress_small_groups`.

Período parcial: se só início ou só fim for informado, aplica o lado correspondente.

---

## 10. Contrato de saída (resumo)

```json
{
  "client_id": 2,
  "periodo": { "inicio": "2026-01", "fim": "2026-06" },
  "metricas": {
    "eventos": 0,
    "trabalhadores_unicos": 0,
    "dias_perdidos": 0.0,
    "horas_perdidas_registradas": 0.0,
    "horas_perdidas_estimadas": 0.0,
    "duracao_media_dias": null,
    "horas_media_evento": null,
    "eventos_por_100_trabalhadores": null,
    "dias_perdidos_por_trabalhador": null
  },
  "metodologia": { "...": "..." },
  "qualidade": {
    "horas": "registrada|estimada|mista|indisponivel",
    "denominador_efetivo": "valido|incompleto|indisponivel",
    "notas": []
  },
  "distribuicao_setor": [],
  "distribuicao_centro_custo": [],
  "distribuicao_cid_grupo": [],
  "limitacoes": []
}
```

---

## 11. Modo shadow

`compare_shadow(db, client_id=…, periodo_inicio=…, periodo_fim=…)` compara:

- legado espelhado de `Analytics.metricas_gerais` (contagens por `nomecompleto`, soma `dias_atestados` / `horas_perdi`);
- resultado canônico do `MetricService`.

Uso: banco temporário + fixtures sintéticas (`tests/fixtures/canonical_metrics.py`).  
**Não** há endpoint público de produção neste lote.

Divergências esperadas:

- identidade (nome vs matrícula/CPF);
- horas (legado soma só `horas_perdi`; canônico separa estimadas);
- taxa de absenteísmo legado **não** é tratada como oficial aqui.

---

## 12. Limitações e indicadores ainda não oficiais

1. Sem deduplicação de reuploads — duplicatas somam (limitação explícita).
2. Identidade de trabalhador ainda frágil sem cadastro estável.
3. Taxa oficial de absenteísmo **não** publicada.
4. Headcount (`efetivo_trabalhadores`) não é inferido do banco neste lote.
5. Dashboard / JS / gráficos **não** alterados.
6. Schema, uploads, usuários, senhas e permissões **não** alterados.

---

## 13. Testes

`tests/test_a01a_canonical_metrics.py` cobre isolamento de cliente, período, totais, médias, divisão por zero, setor/CID ausentes, duplicados, horas ausentes, nulos, inválidos, ausência de fallback de cliente e ausência de PII na saída.
