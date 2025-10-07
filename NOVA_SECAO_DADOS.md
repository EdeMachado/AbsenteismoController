# 🎉 NOVA SEÇÃO: GESTÃO DE DADOS

## 📋 Descrição

Foi implementada uma **seção completa de Gestão de Dados** no AbsenteismoController, semelhante ao PowerBI, permitindo visualizar, editar, adicionar e excluir registros de atestados de forma intuitiva e profissional.

## ✨ Funcionalidades Implementadas

### 🔍 **Visualização de Dados**
- ✅ Tabela completa com todos os registros tratados pelo Python
- ✅ Visualização paginada (50 registros por página)
- ✅ Estatísticas em tempo real no topo da página
- ✅ Interface limpa e profissional

### 🔎 **Busca e Filtros**
- ✅ Busca em tempo real por:
  - Nome do funcionário
  - CPF
  - Setor
  - CID
  - Descrição do CID
- ✅ Filtro por upload específico
- ✅ Filtro por tipo de atestado (Dias/Horas)

### ✏️ **Edição de Registros**
- ✅ Editar qualquer registro existente
- ✅ Formulário completo com todos os campos
- ✅ Validação de dados
- ✅ Atualização em tempo real

### ➕ **Adição de Registros**
- ✅ Criar novos registros manualmente
- ✅ Formulário intuitivo com campos dinâmicos
- ✅ Cálculo automático de dias/horas perdidos
- ✅ Validação de campos obrigatórios

### 🗑️ **Exclusão de Registros**
- ✅ Deletar registros individualmente
- ✅ Confirmação antes de excluir
- ✅ Atualização automática da tabela

### 📊 **Exportação**
- ✅ Exportar dados filtrados para Excel
- ✅ Mantém formatação e todos os campos

## 🎨 Interface

### **Dashboard de Estatísticas**
```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Total Registros │ Atestados Dias  │ Atestados Horas │ Dias Perdidos   │
│      415        │       282       │       133       │      618        │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

### **Tabela de Dados**
```
┌──────────────┬────────────┬──────────┬─────────────┬──────┬──────┬───────────┬─────────┐
│ Funcionário  │    CPF     │  Setor   │    Data     │ Tipo │ CID  │ Dias/Horas│ Ações   │
├──────────────┼────────────┼──────────┼─────────────┼──────┼──────┼───────────┼─────────┤
│ João Silva   │ 123.456... │ Produção │ 15/09/2025  │ Dias │ M54  │  3 dias   │ 👁️ 🗑️  │
│ Maria Santos │ 987.654... │ RH       │ 14/09/2025  │ Horas│ J00  │  4 horas  │ 👁️ 🗑️  │
└──────────────┴────────────┴──────────┴─────────────┴──────┴──────┴───────────┴─────────┘
```

### **Modal de Edição**
- Formulário completo com todos os campos
- Campos dinâmicos (Dias/Horas aparecem conforme o tipo)
- Validação em tempo real
- Design moderno e responsivo

## 🔗 Como Acessar

### **Opção 1: Menu Lateral**
1. Acesse o sistema: `http://localhost:8000`
2. Clique em **"Dados"** no menu lateral

### **Opção 2: Botão "Olhinho" no Upload**
1. Vá para a página de **Upload**
2. No histórico de uploads, clique no ícone **👁️ (olhinho)**
3. Você será direcionado para a página de Dados com o upload selecionado

### **Opção 3: Diretamente**
- Acesse: `http://localhost:8000/dados`

## 📱 Recursos Interativos

### **1. Visualizar Dados**
- Todos os dados tratados pelo Python são exibidos em uma tabela
- Paginação automática para performance
- Formatação automática de CPF, datas, etc.

### **2. Buscar Registros**
```
🔍 [Buscar por nome, CPF, setor, CID...]
```
- Digite qualquer termo
- Resultados filtrados em tempo real
- Busca em múltiplos campos

### **3. Filtrar por Upload**
```
[Todos os uploads ▼] [Todos os tipos ▼]
```
- Selecione um upload específico
- Filtre apenas atestados de Dias ou Horas

### **4. Editar Registro**
```
[Nome do Funcionário *]  [CPF]             [Matrícula]
[Setor]                   [Cargo]           [Gênero]
[Data Afastamento *]      [Data Retorno]    [Tipo *]
[Número de Dias]          [CID]             [Descrição CID]

[Cancelar]  [💾 Salvar]
```

### **5. Adicionar Novo Registro**
```
➕ Novo Registro
```
- Clique no botão no topo
- Preencha o formulário
- Salve e veja o registro aparecer imediatamente

### **6. Exportar para Excel**
```
📊 [Exportar]
```
- Exporta os dados filtrados
- Mantém toda a formatação
- Pronto para análise

## 🛠️ Implementação Técnica

### **Backend (API)**
```python
GET    /api/dados/todos         # Lista todos os dados com filtros
GET    /api/dados/{id}          # Obtém um registro específico
POST   /api/dados               # Cria novo registro
PUT    /api/dados/{id}          # Atualiza registro
DELETE /api/dados/{id}          # Exclui registro
```

### **Frontend**
- `frontend/dados.html` - Interface completa
- `frontend/static/js/dados.js` - Lógica de CRUD
- Design responsivo e moderno
- Validação client-side e server-side

### **Recursos**
- ✅ Paginação eficiente
- ✅ Busca em tempo real
- ✅ Filtros múltiplos
- ✅ Modal de edição
- ✅ Confirmação de exclusão
- ✅ Mensagens de sucesso/erro
- ✅ Loading states
- ✅ Validação de dados

## 📊 Estatísticas Exibidas

```javascript
{
  total_registros: 415,        // Total de registros
  total_atestados_dias: 282,   // Atestados em dias
  total_atestados_horas: 133,  // Atestados em horas
  total_dias_perdidos: 618     // Total de dias perdidos
}
```

## 🎯 Casos de Uso

### **Caso 1: Visualizar dados de um upload específico**
1. Acesse Upload
2. Clique no 👁️ do upload desejado
3. Veja todos os registros daquele upload

### **Caso 2: Corrigir um dado errado**
1. Acesse Dados
2. Busque pelo funcionário
3. Clique em ✏️ Editar
4. Corrija os dados
5. Salve

### **Caso 3: Adicionar atestado manual**
1. Acesse Dados
2. Clique em "➕ Novo Registro"
3. Preencha os dados
4. Salve

### **Caso 4: Remover registro duplicado**
1. Acesse Dados
2. Encontre o registro duplicado
3. Clique em 🗑️
4. Confirme a exclusão

### **Caso 5: Exportar dados filtrados**
1. Acesse Dados
2. Aplique filtros desejados
3. Clique em 📊 Exportar
4. Abra o Excel gerado

## 🎨 Design

### **Princípios Aplicados (CRAP)**
- ✅ **Contraste**: Cards destacados, botões coloridos
- ✅ **Repetição**: Padrões consistentes em toda interface
- ✅ **Alinhamento**: Grid system organizado
- ✅ **Proximidade**: Elementos relacionados agrupados

### **Paleta de Cores**
- 🔵 Primária: #1976D2 (Azul profissional)
- 🟢 Sucesso: #4CAF50 (Verde positivo)
- 🔴 Alerta: #F44336 (Vermelho atenção)
- 🟠 Aviso: #FF9800 (Laranja destaque)

## 🚀 Próximos Passos

Com a seção de Dados completa, agora você pode:

1. ✅ **Visualizar** todos os dados tratados pelo Python
2. ✅ **Editar** registros com erros ou inconsistências
3. ✅ **Adicionar** atestados manualmente quando necessário
4. ✅ **Excluir** registros duplicados ou incorretos
5. ✅ **Exportar** dados para análises externas
6. ✅ **Filtrar** por upload, tipo, período
7. ✅ **Buscar** rapidamente qualquer registro

## 📝 Observações

- Todos os cálculos (dias perdidos, horas perdidas) são feitos automaticamente
- A validação garante que dados obrigatórios sejam preenchidos
- A interface é responsiva e funciona em tablets e mobile
- As alterações são salvas em tempo real no banco de dados
- O sistema mantém o histórico de todos os uploads

## 🎉 Conclusão

A **Seção de Dados** transforma o AbsenteismoController em uma ferramenta completa de gestão, permitindo não apenas visualizar relatórios e gráficos, mas também **gerenciar ativamente** os dados de absenteísmo da sua empresa!

---

**Desenvolvido com ❤️ para GrupoBiomed**

