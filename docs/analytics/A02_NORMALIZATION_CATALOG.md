# A02 — Catálogo de Normalização (somente sugestão)

## Princípios

1. **Nunca** altera o valor original persistido.
2. Normalização ocorre **apenas em memória** para agregação/comparação.
3. Sugestões têm `aplicacao_automatica: false`.
4. **Não** gera SQL, script de `UPDATE` nem migration.
5. **Não** inclui PII.

## Setor

Pipeline em memória:

1. Unicode NFKC  
2. trim  
3. compactação de espaços  
4. chave case-insensitive (`UPPER`)  
5. rótulo proposto (Title Case de apresentação)  
6. valor original preservado no banco (intocado)

### Une automaticamente (variantes de forma)

- `Montagem` / `MONTAGEM` / `  montagem  `

### Não une (semanticamente distintos)

- `Pintura` ≠ `Pintura (Líder)`
- Qualquer diferença além de caixa/espaços/acentos Unicode equivalentes

### Saída agregada

```json
{
  "chave_normalizada": "MONTAGEM",
  "rotulo_proposto": "Montagem",
  "quantidade_variantes": 2,
  "eventos": 44
}
```

## Centro de custo

- Mede cobertura e variantes de forma.
- **Não** inventa CC a partir do setor.
- Se 100% ausente → `status: indisponivel` (não trata `SEM_CENTRO_CUSTO` como dado válido).

## Identidade (estratégia futura — não implementada)

1. Matrícula preferencial  
2. CPF só em camada médica restrita  
3. Identificador pseudonimizado para analytics  
4. Nome como fallback legado  

## Tipos de sugestão neste lote

| tipo | ação típica |
|------|-------------|
| `SETOR_VARIANTE` | Padronizar rótulos futuros no upload |
| `REUPLOAD_COMPETENCIA` | Política de reupload (lote futuro) |
| `CENTRO_CUSTO_AUSENTE` | Incluir CC no layout quando disponível |
| `IDENTIDADE_FRAGIL` | Adotar matrícula preferencial |

## O que não pode ser corrigido automaticamente neste lote

- Histórico de uploads  
- Dicionário persistente de setores  
- Cadastro mestre de funcionários  
- Deduplicação de reuploads  
- Qualquer `UPDATE`/`DELETE` em produção  
