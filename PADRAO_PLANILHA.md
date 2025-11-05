# 📋 Padrão de Planilha - AbsenteismoController

## Como Funciona

O sistema agora **preserva e exibe todas as colunas** da sua planilha original no módulo "Meus Dados", sem fazer transformações complexas.

### 🔄 Fluxo de Processamento

1. **Upload da Planilha**
   - O sistema lê todas as colunas da planilha Excel
   - Salva TODAS as colunas originais em um campo JSON (`dados_originais`)
   - Mapeia apenas os campos principais para compatibilidade com análises

2. **Visualização em "Meus Dados"**
   - Exibe **TODAS as colunas** da planilha original
   - Mantém os nomes das colunas exatamente como estão na planilha
   - Permite edição inline dos campos principais

3. **Exportação**
   - Exporta todas as colunas originais
   - Mantém a estrutura original da planilha

## 📊 Colunas Preservadas

O sistema preserva **TODAS as colunas** da sua planilha, incluindo:

- ✅ Todas as colunas de identificação (CONTRATO, UNIDADE, EMPRESA, etc.)
- ✅ Todas as colunas de centro de custo (DESCCENTROCUSTO1, CENTROCUSTO2, etc.)
- ✅ Todas as colunas de dados (CPF, NOMECOMPLETO, DATAHORA, etc.)
- ✅ Todas as colunas de métricas (NRODIASATESTADO, MÉDIA HORAS POR DIA, etc.)
- ✅ Qualquer outra coluna que você adicionar

## 🎯 Mapeamento de Campos Principais

O sistema mapeia automaticamente alguns campos para compatibilidade:

| Campo Original | Campo Mapeado | Uso |
|---------------|---------------|-----|
| NOMECOMPLETO | nome_funcionario | Análises e relatórios |
| DESCCENTROCUSTO2 | setor | Agrupamentos |
| DESCCID | descricao_cid | Descrições |
| TIPOINFOATEST | tipo_info_atestado | Cálculos |
| NRODIASATESTADO | numero_dias_atestado | Métricas |

**Importante:** Mesmo que o sistema mapeie alguns campos, **TODAS as colunas originais são preservadas e exibidas** no módulo "Meus Dados".

## 📝 Dicas para Padronização

Para facilitar o uso, recomenda-se padronizar a planilha com os seguintes nomes de colunas:

### Colunas Recomendadas (opcional, para melhor compatibilidade)

- `NOMECOMPLETO` ou `NOME_FUNCIONARIO` - Nome do funcionário
- `CPF` - CPF do funcionário
- `DATAHORA` ou `DATA_AFASTAMENTO` - Data do afastamento
- `CID` - Código CID
- `DESCCID` ou `DESCRICAO_CID` - Descrição do CID
- `NRODIASATESTADO` ou `NUMERO_DIAS_ATESTADO` - Quantidade de dias
- `SETOR` ou `DESCCENTROCUSTO2` - Setor/Departamento

**Lembre-se:** Mesmo que você não use esses nomes, o sistema funcionará e preservará todas as suas colunas originais!

## ✅ Vantagens

1. **Flexibilidade Total** - Use qualquer estrutura de planilha
2. **Preservação Completa** - Nenhuma coluna é perdida
3. **Visualização Fiel** - Veja exatamente como está na planilha
4. **Exportação Completa** - Exporte todas as colunas originais

## 🚀 Próximos Passos

1. Faça upload da sua planilha padronizada
2. Acesse o módulo "Meus Dados"
3. Visualize todas as colunas da planilha original
4. Edite campos conforme necessário
5. Exporte os dados quando precisar

---

**Nota:** O sistema é compatível com qualquer estrutura de planilha. Você pode usar os nomes de colunas que preferir, e o sistema preservará tudo!

