# 📊 ANÁLISES CRIADAS PARA RODA DE OURO

## Data: 2025-01-XX
## Cliente: Roda de Ouro (client_id = 4)

---

## 🔍 ANÁLISE DOS DADOS DISPONÍVEIS

### Dados Encontrados:
- ✅ **79 registros** de atestados
- ✅ **Gênero**: Masculino (97.5%) e Feminino (2.5%)
- ✅ **Setores**: 5 setores diferentes (SOLDAGEM, PINTURA, PORTARIA, etc.)
- ✅ **Dias Atestados**: 195 dias totais
- ✅ **Horas por Dia**: Campo disponível (horas_dia)
- ⚠️ **Horas Perdidas**: Campo zerado, mas pode ser calculado (dias × horas_dia)

### Campos Especiais da Roda de Ouro:
- ✅ **Doença**: Nome real da doença
- ✅ **Admissão**: Data de admissão do funcionário
- ✅ **ano** e **mês**: Período do atestado
- ✅ **coerente**: Indica se atestado é coerente
- ✅ **Parecer Médico**: Parecer sobre o atestado

---

## 🆕 NOVAS ANÁLISES IMPLEMENTADAS

### 1. **Horas Perdidas por Gênero** ✅
**Função**: `horas_perdidas_por_genero()`

**O que faz:**
- Calcula horas perdidas por gênero (Masculino/Feminino)
- Se `horas_perdi` estiver zerado, calcula: `dias_atestados × horas_dia`
- Converte horas para semanas (considerando 44h/semana)
- Mostra quantidade de registros por gênero

**Dados retornados:**
```json
{
  "genero": "M",
  "genero_label": "Masculino",
  "horas_perdidas": 2340.0,
  "semanas_perdidas": 53.18,
  "dias_perdidos": 191.0,
  "quantidade": 77
}
```

---

### 2. **Horas Perdidas por Setor** ✅
**Função**: `horas_perdidas_por_setor()`

**O que faz:**
- Calcula horas perdidas por setor
- TOP 10 setores com mais horas perdidas
- Converte para semanas (44h/semana)
- Mostra dias e quantidade de registros

**Dados retornados:**
```json
{
  "setor": "SOLDAGEM",
  "horas_perdidas": 1200.0,
  "semanas_perdidas": 27.27,
  "dias_perdidos": 80.0,
  "quantidade": 25
}
```

---

### 3. **Evolução Mensal de Horas Perdidas** ✅
**Função**: `evolucao_mensal_horas()`

**O que faz:**
- Mostra evolução de horas perdidas mês a mês
- Últimos 12 meses
- Converte para semanas
- Permite identificar tendências

**Dados retornados:**
```json
{
  "mes": "2025-01",
  "horas_perdidas": 200.0,
  "semanas_perdidas": 4.55,
  "dias_perdidos": 15.0,
  "quantidade": 8
}
```

---

### 4. **Análise Detalhada por Gênero** ✅
**Função**: `analise_detalhada_genero()`

**O que faz:**
- Análise completa por gênero
- Percentuais de dias, horas e registros
- Comparação entre gêneros
- Totais gerais

**Dados retornados:**
```json
{
  "total_dias": 195.0,
  "total_horas": 2340.0,
  "total_registros": 79,
  "generos": [
    {
      "genero": "M",
      "genero_label": "Masculino",
      "horas_perdidas": 2280.0,
      "semanas_perdidas": 51.82,
      "dias_perdidos": 191.0,
      "quantidade": 77,
      "percentual_dias": 97.95,
      "percentual_horas": 97.44,
      "percentual_registros": 97.47
    }
  ]
}
```

---

### 5. **Comparativo Dias vs Horas por Gênero** ✅
**Função**: `comparativo_dias_horas_genero()`

**O que faz:**
- Compara dias perdidos vs horas perdidas por gênero
- Permite visualizar diferenças entre gêneros
- Mostra semanas perdidas

**Uso**: Gráfico comparativo (barras lado a lado)

---

### 6. **Horas Perdidas por Setor e Gênero** ✅
**Função**: `horas_perdidas_setor_genero()`

**O que faz:**
- Cruzamento Setor × Gênero
- Mostra horas perdidas em cada combinação
- Identifica padrões específicos

**Exemplo:**
- Setor SOLDAGEM, Masculino: 1000h
- Setor PINTURA, Feminino: 50h

---

## 📈 GRÁFICOS QUE PODEM SER CRIADOS

### 1. **Gráfico de Horas Perdidas por Gênero**
- Tipo: Pizza ou Barras
- Dados: `horas_perdidas_genero`
- Mostra: Distribuição de horas entre M/F

### 2. **Gráfico de Horas Perdidas por Setor**
- Tipo: Barras horizontais
- Dados: `horas_perdidas_setor`
- Mostra: TOP 10 setores

### 3. **Gráfico de Evolução Mensal de Horas**
- Tipo: Linha
- Dados: `evolucao_mensal_horas`
- Mostra: Tendência ao longo do tempo

### 4. **Gráfico Comparativo Dias vs Horas por Gênero**
- Tipo: Barras agrupadas
- Dados: `comparativo_dias_horas_genero`
- Mostra: Comparação lado a lado

### 5. **Gráfico Setor × Gênero × Horas**
- Tipo: Heatmap ou Barras empilhadas
- Dados: `horas_perdidas_setor_genero`
- Mostra: Cruzamento completo

### 6. **Gráfico de Semanas Perdidas**
- Tipo: Barras ou Pizza
- Dados: Qualquer análise com `semanas_perdidas`
- Mostra: Impacto em semanas de trabalho (44h/semana)

---

## 🎯 COMO USAR NO FRONTEND

### No Dashboard (dashboard.js):

```javascript
// Horas perdidas por gênero
if (data.horas_perdidas_genero && data.horas_perdidas_genero.length > 0) {
  const chartData = {
    labels: data.horas_perdidas_genero.map(g => g.genero_label),
    datasets: [{
      label: 'Horas Perdidas',
      data: data.horas_perdidas_genero.map(g => g.horas_perdidas),
      backgroundColor: ['#3498db', '#e74c3c']
    }]
  };
  // Criar gráfico...
}

// Evolução mensal de horas
if (data.evolucao_mensal_horas && data.evolucao_mensal_horas.length > 0) {
  const chartData = {
    labels: data.evolucao_mensal_horas.map(e => e.mes),
    datasets: [{
      label: 'Horas Perdidas',
      data: data.evolucao_mensal_horas.map(e => e.horas_perdidas),
      borderColor: '#3498db',
      fill: false
    }, {
      label: 'Semanas Perdidas',
      data: data.evolucao_mensal_horas.map(e => e.semanas_perdidas),
      borderColor: '#e74c3c',
      fill: false,
      yAxisID: 'y1'
    }]
  };
  // Criar gráfico...
}
```

---

## 📊 MÉTRICAS DISPONÍVEIS

### Por Gênero:
- ✅ Horas perdidas
- ✅ Semanas perdidas (44h/semana)
- ✅ Dias perdidos
- ✅ Quantidade de registros
- ✅ Percentuais (dias, horas, registros)

### Por Setor:
- ✅ Horas perdidas
- ✅ Semanas perdidas
- ✅ Dias perdidos
- ✅ Quantidade de registros

### Temporal:
- ✅ Evolução mensal de horas
- ✅ Evolução mensal de semanas
- ✅ Tendências ao longo do tempo

---

## 🔧 CÁLCULO DE HORAS PERDIDAS

O sistema calcula horas perdidas de 3 formas (em ordem de prioridade):

1. **Se `horas_perdi` > 0**: Usa o valor direto
2. **Se `horas_perdi` = 0 mas tem `horas_dia`**: Calcula `dias_atestados × horas_dia`
3. **Se não tem nenhum**: Usa cálculo SQL `SUM(dias_atestados * horas_dia)`

**Fórmula de Semanas:**
```
semanas_perdidas = horas_perdidas / 44
```

---

## ✅ STATUS DAS IMPLEMENTAÇÕES

- [x] Função `horas_perdidas_por_genero()` - ✅ Implementada
- [x] Função `horas_perdidas_por_setor()` - ✅ Implementada
- [x] Função `evolucao_mensal_horas()` - ✅ Implementada
- [x] Função `analise_detalhada_genero()` - ✅ Implementada
- [x] Função `comparativo_dias_horas_genero()` - ✅ Implementada
- [x] Função `horas_perdidas_setor_genero()` - ✅ Implementada
- [x] Integração no endpoint `/api/dashboard` - ✅ Implementada
- [ ] Gráficos no frontend - ⏳ Pendente (próximo passo)

---

## 🚀 PRÓXIMOS PASSOS

1. **Criar gráficos no frontend** para visualizar as novas análises
2. **Adicionar na página de apresentação** (apresentacao.html)
3. **Criar seção específica** para análises de horas perdidas
4. **Adicionar KPIs** de semanas perdidas no dashboard

---

## 📝 NOTAS IMPORTANTES

- **Semana = 44 horas**: Todas as conversões usam 44 horas por semana
- **Cálculo automático**: Se `horas_perdi` estiver zerado, o sistema calcula automaticamente
- **Filtros aplicáveis**: Todas as análises respeitam filtros de data, funcionário e setor
- **Isolamento**: Todas as análises são isoladas por `client_id` (segurança garantida)

---

**Documento gerado automaticamente após implementação das análises**







