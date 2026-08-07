# A02 — Metodologia do Índice de Qualidade da Base (IQB)

## Definição

IQB ∈ [0, 100] no escopo (`client_id` + período), modo shadow.

## Pesos originais (soma = 100)

| Dimensão        | Peso |
| --------------- | ---: |
| Completude      |   25 |
| Consistência    |   20 |
| Padronização    |   20 |
| Identidade      |   20 |
| Rastreabilidade |   10 |
| Atualidade      |    5 |

## Pesos efetivos e não aplicáveis

Quando uma dimensão IQB é marcada `*_aplicavel=False` no `DataQualityProfile`:

1. entra em `dimensoes_nao_aplicaveis`;
2. seu peso é **redistribuído proporcionalmente** entre as restantes;
3. `pesos_efetivos` somam 100;
4. `metodologia_redistribuicao` descreve o critério.

Campos `centro_custo` / `cid` com `aplicavel=False` **não** entram na média de completude (não penalizam).  
Com `aplicavel=True` e 100% ausente → **penalizam** (não removem a dimensão).

Ausência total **não** retira dimensão do cálculo automaticamente.

## Fórmula

\[
\mathrm{IQB} = \sum_{d \in D_{\mathrm{efetivo}}} \mathrm{score}_d \times \frac{w^{\mathrm{efetivo}}_d}{100}
\]

### Completude

Média das frações de presença dos campos críticos. Inclui CC/CID somente se aplicáveis no perfil.

### Consistência

Penaliza inconsistências por evento (dias negativos, datas, jornada, divergência de horas, período incompatível).

### Padronização

Penaliza eventos em chaves de setor com múltiplas formas literais (após chave sem diacríticos).

### Identidade (por trabalhador aproximado)

\[
\mathrm{score} = 100 \times \frac{1{,}0\cdot T_{mat} + 0{,}6\cdot T_{cpf} + 0{,}25\cdot T_{nome}}{T}
\]

Cobertura por evento é complementar e **não** alimenta o IQB (evita domínio por recorrentes).

### Rastreabilidade

Nome de arquivo + data de processamento; penaliza múltiplos uploads por competência; teto reduzido se hash indisponível (schema).  
Múltiplos uploads = possível reupload / duplicidade **não** confirmada.

### Atualidade

Requer `data_referencia` na saída. Score por lag do último `data_upload`:

| Lag        | Score |
| ---------- | ----: |
| ≤ 30 dias  |   100 |
| ≤ 90 dias  |    80 |
| ≤ 180 dias |    60 |
| > 180 dias |    30 |

Também informa `ultimo_periodo_valido` e `diferenca_meses_vs_referencia`.

## Classificação

| Faixa    | Classe    |
| -------- | --------- |
| 90–100   | excelente |
| 80–89,99 | boa       |
| 65–79,99 | regular   |
| 50–64,99 | baixa     |
| < 50     | crítica   |

## Limitações

- Shadow; sem correção histórica.
- Hash de arquivo inexistente no modelo.
- Identidade aproximada; fragmentação possível.
- Sobreposição: `registros_com_sobreposicao_potencial` (máx. 1/registro).
- Soma de grupos CID suprimidos ≠ efetivo único global.
