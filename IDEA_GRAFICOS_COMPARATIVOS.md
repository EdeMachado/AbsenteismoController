# 📊 IDEIAS - GRÁFICOS COMPARATIVOS E COMBINADOS

## 🎯 SUGESTÕES PARA IMPLEMENTAÇÃO FUTURA

### 1. Gráficos Comparativos Entre Meses

**Objetivo:** Comparar períodos diferentes (ex: mês atual vs mês anterior, trimestre vs trimestre anterior)

**Exemplos:**
- Comparativo Janeiro 2025 vs Janeiro 2024
- Comparativo Q1 2025 vs Q1 2024
- Comparativo últimos 3 meses vs 3 meses anteriores
- Comparativo mês atual vs média dos últimos 6 meses

**Métricas a comparar:**
- Dias perdidos
- Horas perdidas
- Número de atestados
- Funcionários afetados
- TOP CIDs
- TOP Setores

**Visualização:**
- Gráfico de barras lado a lado (mês atual vs mês anterior)
- Gráfico de barras agrupadas (comparar múltiplos meses)
- Indicadores de variação percentual (+/- %)

---

### 2. Gráficos Combinados (Barra + Linha)

**Objetivo:** Mostrar valores absolutos (barras) e tendência/variação (linha)

**Exemplos:**

#### A) Barras Verticais + Linha de Tendência
- **Barras:** Dias perdidos por mês (valores absolutos)
- **Linha:** Tendência/regressão linear (mostra se está subindo ou descendo)
- **Útil para:** Ver valores reais e identificar tendência

#### B) Barras Verticais + Linha de Variação Percentual
- **Barras:** Horas perdidas por mês
- **Linha:** Variação percentual mês a mês (ex: +5%, -10%, +2%)
- **Útil para:** Ver valores e identificar se está melhorando ou piorando

#### C) Barras Verticais + Linha de Meta
- **Barras:** Dias perdidos por mês
- **Linha:** Meta estabelecida (ex: meta de 100 dias/mês)
- **Útil para:** Comparar performance real vs meta

#### D) Barras Verticais + Linha de Média Móvel
- **Barras:** Dias perdidos por mês
- **Linha:** Média móvel de 3 ou 6 meses (suaviza variações)
- **Útil para:** Ver tendência de longo prazo sem ruído

---

### 3. Gráficos de Variação Percentual

**Objetivo:** Mostrar se está melhorando ou piorando

**Visualização:**
- Gráfico de barras coloridas:
  - **Verde:** Redução (melhora) - ex: -10%
  - **Vermelho:** Aumento (piora) - ex: +15%
  - **Amarelo:** Sem mudança significativa - ex: ±2%

**Métricas:**
- Variação de dias perdidos mês a mês
- Variação de horas perdidas mês a mês
- Variação de número de atestados
- Variação por setor
- Variação por CID

---

### 4. Gráficos de Tendência com Indicadores

**Objetivo:** Mostrar claramente se está subindo ou descendo

**Visualização:**
- Gráfico de linha com setas/indicadores:
  - ⬆️ **Seta para cima:** Tendência de aumento
  - ⬇️ **Seta para baixo:** Tendência de redução
  - ➡️ **Seta horizontal:** Estável

**Cálculo:**
- Comparar últimos 3 meses vs 3 meses anteriores
- Se média aumentou → ⬆️
- Se média diminuiu → ⬇️
- Se média similar → ➡️

---

## 💡 IMPLEMENTAÇÃO TÉCNICA

### Biblioteca: Chart.js (já está sendo usada)

**Gráfico Combinado (Bar + Line):**
```javascript
{
    type: 'bar', // Barras principais
    data: {
        datasets: [
            {
                type: 'bar', // Dias perdidos
                label: 'Dias Perdidos',
                data: [...],
                yAxisID: 'y'
            },
            {
                type: 'line', // Linha de tendência
                label: 'Tendência',
                data: [...], // Valores calculados (média móvel, regressão, etc)
                yAxisID: 'y',
                borderColor: '#FF0000',
                backgroundColor: 'transparent',
                pointRadius: 0,
                tension: 0.4
            }
        ]
    }
}
```

**Gráfico Comparativo:**
```javascript
{
    type: 'bar',
    data: {
        labels: ['Jan/2025', 'Jan/2024'],
        datasets: [
            {
                label: 'Dias Perdidos',
                data: [150, 180], // Mês atual vs mês anterior
                backgroundColor: ['#1a237e', '#556B2F']
            }
        ]
    }
}
```

---

## 📋 ONDE IMPLEMENTAR

### Dashboard (`frontend/static/js/dashboard.js`)
- Nova função: `renderizarChartComparativoMeses()`
- Nova função: `renderizarChartCombinadoBarraLinha()`
- Nova função: `renderizarChartVariacaoPercentual()`

### Apresentação (`frontend/static/js/apresentacao.js`)
- Adicionar slides comparativos
- Slide: "Comparativo Mensal"
- Slide: "Tendência de Evolução"

### Backend (`backend/main.py`)
- Nova rota: `/api/comparativo-meses`
- Nova função em `analytics.py`: `comparativo_meses()`
- Nova função em `analytics.py`: `calcular_tendencia()`

---

## 🎨 EXEMPLOS VISUAIS

### Gráfico Combinado (Barra + Linha)
```
Dias Perdidos
    |
200 |     ████
    |    ████  ╱
150 |   ████  ╱
    |  ████ ╱
100 | ████╱
    |─────╱─────
    Jan  Fev  Mar  Abr
    Barras: Dias perdidos
    Linha: Tendência (média móvel)
```

### Gráfico Comparativo
```
Dias Perdidos
    |
200 |     ████
    |     ████
150 |  ████
    |  ████
100 |
    |─────
    Jan/2025  Jan/2024
```

---

## ✅ PRÓXIMOS PASSOS (QUANDO IMPLEMENTAR)

1. **Definir quais comparações são mais úteis**
   - Mês atual vs mês anterior?
   - Últimos 3 meses vs 3 meses anteriores?
   - Mês atual vs mesmo mês do ano anterior?

2. **Definir métricas prioritárias**
   - Dias perdidos?
   - Horas perdidas?
   - Número de atestados?
   - Todos?

3. **Criar funções no backend**
   - `comparativo_meses(client_id, mes1, mes2)`
   - `calcular_tendencia(client_id, meses)`
   - `variacao_percentual(client_id, periodo1, periodo2)`

4. **Implementar no frontend**
   - Gráficos no dashboard
   - Slides na apresentação
   - Indicadores visuais (setas, cores)

---

## 📝 NOTAS

- Chart.js suporta gráficos combinados nativamente
- Pode usar múltiplos eixos Y para diferentes escalas
- Cores podem indicar melhora/piora automaticamente
- Tooltips podem mostrar variação percentual

---

**Marcado para implementação futura! 🚀**


