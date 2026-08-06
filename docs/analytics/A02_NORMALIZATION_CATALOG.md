# A02 — Catálogo de Normalização (somente sugestão)

## Princípios

1. Nunca altera o valor original persistido.
2. Normalização só em memória.
3. `aplicacao_automatica: false`.
4. Sem SQL / UPDATE / migration.
5. Sem PII.

## Setor — duas representações

| Representação | Uso |
|---------------|-----|
| Valor original | Intocado no banco |
| Chave comparável | NFKC → remoção de diacríticos (NFKD) → trim → espaços → casefold |

### Mesmo grupo de forma

- `Elétrica` / `ELETRICA` / `eletrica`
- `Manutenção` / `MANUTENCAO` / `manutenção`

### Não une (semântica)

- `Pintura` ≠ `Pintura (Líder)`

## Rótulo proposto

1. Variante **mais frequente**
2. Empate: ordem lexicográfica determinística
3. Preserva siglas (`RH`, `TI`, `PCP`) — não força `Rh`/`Ti`/`Pcp`
4. `necessita_validacao_humana=true`
5. `proposta_definitiva=false`
6. Lista apenas variantes agregadas (`rotulo` + `eventos`), não linhas

## Centro de custo

- Cobertura e variantes de forma.
- Não inventa a partir do setor.
- Aplicável + 100% ausente → penaliza.
- `centro_custo_aplicavel=False` → não penaliza.

## Uploads

Auditoria independente por `Upload.client_id` (inclui zero eventos):

- válidos na janela
- sem período / malformados
- zero eventos
- excluídos da janela por período inválido (visíveis em `periodos_invalidos`)

### Múltiplos uploads na competência

- `multiplos_uploads_competencia`
- `possivel_reupload`
- `duplicidade_nao_confirmada`

> A presença de mais de um upload na mesma competência exige revisão, mas não comprova duplicidade sem hash ou assinatura do conteúdo.

`duplicidade_confirmada` permanece indisponível sem hash.

## CID — supressão

`GRUPO_SUPRIMIDO` reporta:

- `grupos_suprimidos`
- `soma_contagens_por_grupo` (pode doble-contar pessoas em vários grupos)
- `trabalhadores_unicos_globais`

Não interpretar a soma por grupo como efetivo total.

## Tipos de sugestão

| tipo | nota |
|------|------|
| `SETOR_VARIANTE` | padronizar uploads futuros |
| `MULTIPLOS_UPLOADS_COMPETENCIA` | revisão; não confirma duplicidade |
| `CENTRO_CUSTO_AUSENTE` | se aplicável |
| `IDENTIDADE_FRAGIL` | matrícula preferencial |
