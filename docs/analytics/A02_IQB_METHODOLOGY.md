# A02 — Metodologia do Índice de Qualidade da Base (IQB)

## Definição

O IQB é um indicador composto **0–100** que resume a qualidade analítica dos eventos de absenteísmo no escopo (`client_id` + período), em modo shadow.

## Pesos padrão (soma = 100)

| Dimensão        | Peso |
| --------------- | ---: |
| Completude      |   25 |
| Consistência    |   20 |
| Padronização    |   20 |
| Identidade      |   20 |
| Rastreabilidade |   10 |
| Atualidade      |    5 |

Pesos são configuráveis via `IQBWeights` / argumento `weights` em `analyze()`. Devem somar 100.

## Fórmula

\[
\mathrm{IQB} = \sum_{d \in D} \mathrm{score}_d \times \frac{w_d}{100}
\]

Cada `score_d` ∈ [0, 100].

### Completude

Média da presença (fração) de campos críticos por evento: setor, dias, identidade útil, vínculo upload, período, jornada, horas (registrada **ou** estimável), data; e, se aplicável, centro de custo (quando a dimensão não está `indisponivel`) e CID.

### Consistência

Penaliza inconsistências por evento: dias negativos, data final < inicial, data futura, jornada inválida, divergência `|dias×jornada − horas_registradas| > 0,5`, período incompatível com a data do evento.

### Padronização

Penaliza eventos cuja chave de setor (normalizada) possui **mais de uma** forma literal (variantes de caixa/espaços/acentos). Não une rótulos semanticamente distintos.

### Identidade

\[
\mathrm{score} = 100 \times \frac{1{,}0\cdot N_{mat} + 0{,}6\cdot N_{cpf} + 0{,}25\cdot N_{nome}}{N}
\]

Risco qualitativo: baixo / moderado / alto / crítico (sem expor valores).

### Rastreabilidade

Combina disponibilidade de nome de arquivo e data de processamento; penaliza múltiplos uploads por competência; teto reduzido quando hash de arquivo **não existe no schema**.

### Atualidade

Com base no lag (dias) do último `data_upload` vs data de referência:

| Lag        | Score |
| ---------- | ----: |
| ≤ 30 dias  |   100 |
| ≤ 90 dias  |    80 |
| ≤ 180 dias |    60 |
| > 180 dias |    30 |

## Classificação

| Faixa       | Classe     |
| ----------- | ---------- |
| 90–100      | excelente  |
| 80–89,99    | boa        |
| 65–79,99    | regular    |
| 50–64,99    | baixa      |
| < 50        | crítica    |

## O que é fato vs sugestão

| Fato (contagens/percentuais) | Sugestão (não automática) |
| ---------------------------- | ------------------------- |
| Ausências, inválidos, variantes | `sugestoes[]` com `aplicacao_automatica: false` |
| Alertas agregados            | Ações futuras de upload   |

## Limitações

- Shadow: não corrige histórico.
- Sem hash de arquivo no modelo `Upload`.
- Identidade aproximada (A01); sem fuzzy matching.
- Sobreposição de intervalos é heurística agregada.
- IQB não substitui auditoria clínica nem taxa oficial de absenteísmo.
