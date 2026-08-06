# A01-A — Contrato de Métricas Canônicas (modo conferência / shadow)

**Status:** shadow — não substitui dashboard, gráficos nem `analytics.py` em produção.  
**Branch:** `feat/a01a-canonical-metrics-shadow`  
**Serviço:** `backend/services/metric_service.py`  
**Comparação local:** `backend/services/shadow_compare.py` + `scripts/shadow_compare_metrics.py`

---

## 1. Objetivo

Calcular métricas candidatas a oficiais em camada isolada, para conferência com os resultados atuais **sem** alterar visualizações.

Assinatura preferida:

```python
service = MetricService(db)
result = service.compute(client_id=..., periodo_inicio=..., periodo_fim=...)
```

- `db` fica no construtor; `compute()` **não** recebe nem altera `self.db`.
- `client_id` obrigatório (`> 0`); **sem** fallback `client_id=1`.
- Independente de HTTP. Sem PII na saída.

---

## 2. Evento bruto vs analiticamente válido

| Conceito | Definição |
|----------|-----------|
| `eventos_brutos` / `eventos` | Contagem de linhas `Atestado` no escopo (alias `eventos` = brutos, compat shadow) |
| `eventos_validos_para_dias` | `dias_atestados` numérico e `>= 0` (zero é válido) |
| `eventos_com_dias_invalidos` | nulo, não-numérico ou negativo — **não** entram no total de dias |
| `eventos_com_horas_invalidas` | `horas_perdi` negativa ou não-numérica — registrada na qualidade |
| `eventos_sem_identidade` | sem matrícula, CPF nem nome utilizável |
| `eventos_sem_horas` | sem horas registradas e sem estimativa possível |

Registros inválidos **não** são excluídos da contagem bruta; entram nas contagens de qualidade. Não há filtro silencioso.

### Valores: nulo, zero, negativo, texto

| Valor | Dias | Horas registradas |
|-------|------|-------------------|
| `null` / não-numérico | inválido | inválido (horas) / ausência |
| `0` | válido (contribui 0) | não registrada (tenta estimativa) |
| `< 0` | inválido | inválido |
| `> 0` | válido | registrada |

---

## 3. Período

- Formato obrigatório `YYYY-MM` quando informado (mês 01–12).
- **Sem** normalização de formatos ambíguos (`2026-6` → `ValueError`).
- `inicio > fim` → `ValueError`.
- Período ausente (`None`) é permitido (sem filtro temporal).
- Com filtro ativo: `mes_referencia` nula, vazia ou malformada **não** entra no intervalo.

---

## 4. Identidade aproximada

Não é identidade canônica estável. Função interna `worker_identity_parts` / `worker_identity_key`:

1. matrícula → 2. CPF (dígitos) → 3. nome normalizado → 4. nenhum

**A chave interna nunca sai na resposta.**

Saída:

```json
"qualidade_identidade": {
  "metodo": "aproximado",
  "por_matricula": 0,
  "por_cpf": 0,
  "somente_por_nome": 0,
  "sem_identificador": 0,
  "confiabilidade": "alta|media|baixa"
}
```

**Fragmentação:** o mesmo nome sob chaves distintas gera nota em `limitacoes` — **sem** fuzzy matching / unificação neste lote. Reuploads duplicados continuam somando.

---

## 5. Horas registradas vs estimadas

| Campo | Conteúdo |
|-------|----------|
| `horas_perdidas_registradas` | Soma `horas_perdi > 0` |
| `horas_perdidas_estimadas` | Soma `dias * horas_dia` só quando não há registrada válida |
| `horas_registradas_media_por_evento` | Média **somente** sobre eventos com horas registradas |
| `eventos_com_horas_registradas` | Contagem |
| `horas_estimadas_media_por_evento` | Média **somente** sobre eventos estimados |
| `eventos_com_horas_estimadas` | Contagem |
| `eventos_sem_horas` | Contagem |

**Não** existe média genérica única (`horas_media_evento` removido).  
`qualidade.horas`: `registrada` | `estimada` | `mista` | `indisponivel`.

---

## 6. Grupo alfabético CID (não é capítulo)

- Campo: `distribuicao_grupo_alfabetico_cid` / chave `grupo_alfabetico_cid`.
- Função: `cid_letra_inicial` (letra A–Z; `SEM_CID` / `OUTROS`).
- **Não** é capítulo oficial CID-10/OMS. Agrupamento oficial por capítulo = evolução futura.

---

## 7. Setor vs centro de custo

Campos e distribuições separados. Sem sinônimo/fallback entre eles.

---

## 8. Supressão LGPD de grupos pequenos

Com `suppress_small_groups=True` e `small_group_threshold > 0`:

- rótulos com `0 < trabalhadores_unicos < limiar` **não** aparecem;
- valores agregados vão para um único bucket `GRUPO_SUPRIMIDO` (com `grupos_suprimidos`);
- totais de eventos/dias da distribuição preservados;
- sem inferência do rótulo individual.

Aplica-se a setor, centro de custo e grupo alfabético CID. Limiar `<= 0` → `ValueError`.

---

## 9. Demais métricas

| Métrica | Notas |
|---------|--------|
| `trabalhadores_unicos` | Cardinalidade de chaves aproximadas |
| `dias_perdidos` | Soma só de dias válidos |
| `duracao_media_dias` | Média dos eventos com dias `> 0` |
| `eventos_por_100_trabalhadores` | Só com `efetivo_trabalhadores > 0` externo |
| `dias_perdidos_por_trabalhador` | `null` se 0 trabalhadores |

Taxa oficial de absenteísmo **não** implementada (horas previstas não comprovadas).

---

## 10. Shadow compare — proteções

- Não registra endpoint; não é importado por `backend/main.py`; não roda no import.
- Script exige `--fixtures` **ou** `--db-path` explícito (sem default de produção).
- SQLite via path: modo leitura (`mode=ro` + `PRAGMA query_only`).
- Saída só agregados; assertiva anti-PII; chaves internas bloqueadas.

```bash
PYTHONPATH=. python3 scripts/shadow_compare_metrics.py --fixtures --client-id 2 --inicio 2026-01 --fim 2026-06
```

---

## 11. Limitações

1. Reuploads / duplicatas somam (sem dedupe).
2. Identidade aproximada e fragmentável.
3. Sem taxa oficial.
4. Sem capítulo CID oficial.
5. Dashboard / auth / schema / uploads intocados.
