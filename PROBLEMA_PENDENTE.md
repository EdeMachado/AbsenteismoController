# Problema Pendente - Roda de Ouro

## Data: 13/11/2025

### Problema
O campo `nomecompleto` não está sendo preenchido após upload da planilha da Roda de Ouro (cliente 4).

### Situação Atual
- Mapeamento configurado: "Nome completo" -> nomecompleto
- Dados são salvos no banco, mas `nomecompleto` fica vazio
- Outros campos como `setor` são salvos corretamente
- Sistema mostra "Nenhum dado encontrado" ao tentar gerar gráfico com campo `nomecompleto`

### Alterações Realizadas
1. ✅ Implementado fuzzy matching para detecção automática de colunas similares
2. ✅ Melhorada função `get_valor` para buscar valores com variações de nome
3. ✅ Adicionado mapeamento padrão que inclui "NOME COMPLETO" -> "NOMECOMPLETO"
4. ✅ Normalização de nomes de colunas (remove espaços, acentos, case-insensitive)
5. ✅ Logs detalhados no console do servidor para debug

### Próximos Passos
- Verificar logs do servidor durante upload para ver se mapeamento está sendo aplicado
- Testar se o problema é na detecção da coluna ou na busca do valor após mapeamento
- Verificar se a coluna na planilha está realmente como "NOME COMPLETO" ou outra variação
- Possivelmente adicionar fallback para buscar valores diretamente do DataFrame original

### Arquivos Modificados
- `backend/excel_processor.py` - Melhorias no mapeamento e busca de valores
- `backend/main.py` - Melhorias na extração do mapeamento customizado

