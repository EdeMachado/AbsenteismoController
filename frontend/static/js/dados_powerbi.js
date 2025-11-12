/**
 * Análise de Dados - Estilo PowerBI
 * Interface simples e intuitiva
 */

let allData = [];
let filteredData = [];
let activeFilters = {};
let todasColunas = []; // Todas as colunas da planilha original
let chartTendenciaMensal = null;
let chartTendenciaAcumulado = null;
let anoSelecionado = null;
let mesSelecionado = null;

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (!clientId) {
        showError('Selecione um cliente na aba "Clientes" para visualizar e editar os dados.');
        renderEmptyTable();
        updateStats();
        return;
    }
    loadData(clientId);
    setupEventListeners();
    carregarAnosDisponiveis();
});

function renderEmptyTable() {
    const tableBody = document.getElementById('tableBody');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="12" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    Selecione um cliente na aba "Clientes" para carregar os dados.
                </td>
            </tr>
        `;
    }
}

// Carregar dados
async function loadData(clientId) {
    try {
        // Verifica se há upload_id na URL
        const urlParams = new URLSearchParams(window.location.search);
        const uploadId = urlParams.get('upload_id');
        
        let url = `/api/dados/todos?client_id=${clientId}`;
        if (uploadId) {
            url += `&upload_id=${uploadId}`;
        }
        
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Erro HTTP:', response.status, errorText);
            throw new Error(`Erro ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        
        allData = data.dados || [];
        filteredData = [...allData];
        
        // Detecta todas as colunas dinamicamente a partir dos dados
        // PRIORIDADE: usa a ordem que veio do backend (colunas_originais)
        if (data.colunas_originais && data.colunas_originais.length > 0) {
            // Usa as colunas originais da planilha EXATAMENTE na ordem que veio
            todasColunas = data.colunas_originais;
        } else if (allData.length > 0) {
            // Se não vier do backend, detecta a partir dos dados
            todasColunas = Object.keys(allData[0]);
            // Remove campos internos do sistema
            todasColunas = todasColunas.filter(col => 
                !['id', 'upload_id', 'dados_originais'].includes(col.toLowerCase())
            );
        } else {
            // Fallback para colunas padrão da planilha padronizada (ORDEM EXATA)
            todasColunas = [
                'nomecompleto',      // 1. NOMECOMPLETO
                'descricao_atestad', // 2. DESCRIÇÃO ATESTAD
                'dias_atestados',    // 3. DIAS ATESTADOS
                'cid',               // 4. CID
                'diagnostico',       // 5. DIAGNÓSTICO
                'centro_custo',      // 6. CENTROCUST
                'setor',             // 7. setor
                'motivo_atestado',   // 8. motivo atestado
                'escala',            // 9. escala
                'horas_dia',         // 10. Horas/dia
                'horas_perdi'        // 11. Horas perdi
            ];
        }
        
        // Ordena colunas EXATAMENTE na ordem da planilha padronizada
        const colunasPrincipais = [
            'nomecompleto',      // 1. NOMECOMPLETO
            'descricao_atestad', // 2. DESCRIÇÃO ATESTAD
            'dias_atestados',    // 3. DIAS ATESTADOS
            'cid',               // 4. CID
            'diagnostico',       // 5. DIAGNÓSTICO
            'centro_custo',      // 6. CENTROCUST
            'setor',             // 7. setor
            'motivo_atestado',   // 8. motivo atestado
            'escala',            // 9. escala
            'horas_dia',         // 10. Horas/dia
            'horas_perdi'        // 11. Horas perdi
        ];
        const colunasOrdenadas = [];
        
        // Se veio do backend com colunas_originais, usa EXATAMENTE essa ordem
        // Não tenta reordenar - usa a ordem que veio da planilha
        if (data.colunas_originais && data.colunas_originais.length > 0) {
            // Já está na ordem correta, não precisa fazer nada
            // todasColunas já foi definido acima
        } else {
            // Se não veio do backend, ordena usando a ordem padrão
            const ordemFinal = [];
            
            // Adiciona colunas principais na ordem exata
            colunasPrincipais.forEach(col => {
                if (todasColunas.includes(col)) {
                    ordemFinal.push(col);
                }
            });
            
            // Adiciona as demais colunas que não estão na lista principal (se houver)
            todasColunas.forEach(col => {
                if (!ordemFinal.includes(col)) {
                    ordemFinal.push(col);
                }
            });
            
            todasColunas = ordemFinal.length > 0 ? ordemFinal : colunasPrincipais;
        }
        
        updateStats();
        renderTable();
        carregarAnosDisponiveis();
        
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        showError('Erro ao carregar dados');
    }
}

// Carregar anos disponíveis nos dados
function carregarAnosDisponiveis() {
    const anos = new Set();
    allData.forEach(reg => {
        if (reg.mes_referencia) {
            const ano = reg.mes_referencia.split('-')[0];
            if (ano) anos.add(ano);
        }
    });
    
    const anoSelect = document.getElementById('anoSelect');
    if (!anoSelect) return;
    
    // Limpa opções existentes (exceto "Todos os anos")
    while (anoSelect.children.length > 1) {
        anoSelect.removeChild(anoSelect.lastChild);
    }
    
    // Adiciona anos em ordem decrescente
    Array.from(anos).sort((a, b) => b - a).forEach(ano => {
        const option = document.createElement('option');
        option.value = ano;
        option.textContent = ano;
        anoSelect.appendChild(option);
    });
}

// Selecionar mês via aba
function selecionarMes(mes) {
    mesSelecionado = mes;
    
    // Atualiza o select de mês
    const mesSelect = document.getElementById('mesSelect');
    if (mesSelect) {
        mesSelect.value = mes;
    }
    
    // Atualiza visual das abas
    document.querySelectorAll('.mes-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.mes === mes) {
            tab.classList.add('active');
        }
    });
    
    atualizarPeriodo();
}

// Atualizar período (mês/ano)
function atualizarPeriodo() {
    const anoSelect = document.getElementById('anoSelect');
    const mesSelect = document.getElementById('mesSelect');
    
    anoSelecionado = anoSelect ? anoSelect.value : null;
    mesSelecionado = mesSelect ? mesSelect.value : null;
    
    // Atualiza visual das abas de mês
    document.querySelectorAll('.mes-tab').forEach(tab => {
        if (mesSelecionado && tab.dataset.mes === mesSelecionado) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    // Se apenas ano foi selecionado (sem mês), mostra tendência anual E filtra tabela
    if (anoSelecionado && !mesSelecionado) {
        mostrarTendenciaAnual(anoSelecionado);
        filtrarPorPeriodo(); // Filtra a tabela também
    } else {
        fecharTendencia();
        filtrarPorPeriodo();
    }
}

// Filtrar dados por período
function filtrarPorPeriodo() {
    filteredData = allData.filter(reg => {
        if (!reg.mes_referencia) return false;
        
        const [ano, mes] = reg.mes_referencia.split('-');
        
        if (anoSelecionado && ano !== anoSelecionado) return false;
        if (mesSelecionado && mes !== mesSelecionado) return false;
        
        return true;
    });
    
    updateStats();
    renderTable();
}

// Mostrar tendência anual
async function mostrarTendenciaAnual(ano) {
    const tendenciaDiv = document.getElementById('tendenciaAnual');
    if (!tendenciaDiv) return;
    
    tendenciaDiv.classList.add('show');
    
    // Filtra dados do ano
    const dadosAno = allData.filter(reg => {
        if (!reg.mes_referencia) return false;
        return reg.mes_referencia.startsWith(ano + '-');
    });
    
    // Agrupa por mês
    const dadosPorMes = {};
    const meses = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
    const nomesMeses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    
    meses.forEach(mes => {
        dadosPorMes[mes] = {
            registros: 0,
            dias: 0,
            horas: 0
        };
    });
    
    dadosAno.forEach(reg => {
        const mes = reg.mes_referencia ? reg.mes_referencia.split('-')[1] : null;
        if (mes && dadosPorMes[mes]) {
            dadosPorMes[mes].registros++;
            dadosPorMes[mes].dias += parseFloat(reg.dias_atestados || reg.numero_dias_atestado || 0);
            dadosPorMes[mes].horas += parseFloat(reg.horas_perdi || reg.horas_perdidas || 0);
        }
    });
    
    // Prepara dados para gráficos
    const labels = nomesMeses;
    const dadosRegistros = meses.map(mes => dadosPorMes[mes].registros);
    const dadosDias = meses.map(mes => dadosPorMes[mes].dias);
    const dadosHoras = meses.map(mes => dadosPorMes[mes].horas);
    
    // Calcula acumulado
    const acumuladoDias = [];
    const acumuladoHoras = [];
    let totalDias = 0;
    let totalHoras = 0;
    
    meses.forEach(mes => {
        totalDias += dadosPorMes[mes].dias;
        totalHoras += dadosPorMes[mes].horas;
        acumuladoDias.push(totalDias);
        acumuladoHoras.push(totalHoras);
    });
    
    // Cria gráfico de tendência mensal
    criarGraficoTendenciaMensal(labels, dadosRegistros, dadosDias, dadosHoras);
    
    // Cria gráfico de acumulado
    criarGraficoAcumulado(labels, acumuladoDias, acumuladoHoras);
    
    // Gera análise macro
    gerarAnaliseMacro(dadosAno, dadosPorMes, ano);
}

// Criar gráfico de tendência mensal
function criarGraficoTendenciaMensal(labels, registros, dias, horas) {
    const ctx = document.getElementById('chartTendenciaMensal');
    if (!ctx) return;
    
    if (chartTendenciaMensal) {
        chartTendenciaMensal.destroy();
    }
    
    chartTendenciaMensal = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Registros',
                    data: registros,
                    borderColor: '#00bcf2',
                    backgroundColor: 'rgba(0, 188, 242, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Dias Perdidos',
                    data: dias,
                    borderColor: '#ff9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                },
                {
                    label: 'Horas Perdidas',
                    data: horas,
                    borderColor: '#4caf50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y2'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Tendência Mensal - ' + anoSelecionado
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Registros'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Dias'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                },
                y2: {
                    type: 'linear',
                    display: false
                }
            }
        }
    });
}

// Criar gráfico de acumulado
function criarGraficoAcumulado(labels, diasAcumulado, horasAcumulado) {
    const ctx = document.getElementById('chartTendenciaAcumulado');
    if (!ctx) return;
    
    if (chartTendenciaAcumulado) {
        chartTendenciaAcumulado.destroy();
    }
    
    chartTendenciaAcumulado = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Dias Acumulado',
                    data: diasAcumulado,
                    backgroundColor: 'rgba(0, 188, 242, 0.6)',
                    borderColor: '#00bcf2',
                    borderWidth: 1
                },
                {
                    label: 'Horas Acumulado',
                    data: horasAcumulado,
                    backgroundColor: 'rgba(255, 152, 0, 0.6)',
                    borderColor: '#ff9800',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Acumulado Anual - ' + anoSelecionado
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Valor Acumulado'
                    }
                }
            }
        }
    });
}

// Gerar análise macro
function gerarAnaliseMacro(dadosAno, dadosPorMes, ano) {
    const container = document.getElementById('analiseMacroContent');
    if (!container) return;
    
    const meses = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
    
    // Calcula totais
    const totalRegistros = dadosAno.length;
    const totalDias = dadosAno.reduce((sum, reg) => sum + parseFloat(reg.dias_atestados || reg.numero_dias_atestado || 0), 0);
    const totalHoras = dadosAno.reduce((sum, reg) => sum + parseFloat(reg.horas_perdi || reg.horas_perdidas || 0), 0);
    const mediaMensalRegistros = totalRegistros / 12;
    const mediaMensalDias = totalDias / 12;
    
    // Encontra mês com maior absenteísmo
    let mesMaior = null;
    let maiorDias = 0;
    Object.keys(dadosPorMes).forEach(mes => {
        if (dadosPorMes[mes].dias > maiorDias) {
            maiorDias = dadosPorMes[mes].dias;
            mesMaior = mes;
        }
    });
    
    const nomesMeses = {
        '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março', '04': 'Abril',
        '05': 'Maio', '06': 'Junho', '07': 'Julho', '08': 'Agosto',
        '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
    };
    
    // Calcula tendência (comparando primeira e segunda metade do ano)
    const primeiraMetade = meses.slice(0, 6).reduce((sum, mes) => sum + dadosPorMes[mes].dias, 0);
    const segundaMetade = meses.slice(6, 12).reduce((sum, mes) => sum + dadosPorMes[mes].dias, 0);
    const variacao = primeiraMetade > 0 ? ((segundaMetade - primeiraMetade) / primeiraMetade * 100).toFixed(1) : '0.0';
    const tendencia = parseFloat(variacao) > 0 ? 'Aumento' : parseFloat(variacao) < 0 ? 'Redução' : 'Estável';
    
    container.innerHTML = `
        <div class="analise-item">
            <div class="analise-item-title">Total de Registros</div>
            <div class="analise-item-value">${totalRegistros.toLocaleString('pt-BR')}</div>
            <div class="analise-item-desc">Registros de atestados em ${ano}</div>
        </div>
        <div class="analise-item">
            <div class="analise-item-title">Total de Dias Perdidos</div>
            <div class="analise-item-value">${totalDias.toFixed(1)}</div>
            <div class="analise-item-desc">Dias de absenteísmo no ano</div>
        </div>
        <div class="analise-item">
            <div class="analise-item-title">Total de Horas Perdidas</div>
            <div class="analise-item-value">${totalHoras.toFixed(1)}</div>
            <div class="analise-item-desc">Horas de absenteísmo no ano</div>
        </div>
        <div class="analise-item">
            <div class="analise-item-title">Média Mensal de Registros</div>
            <div class="analise-item-value">${mediaMensalRegistros.toFixed(1)}</div>
            <div class="analise-item-desc">Média de atestados por mês</div>
        </div>
        <div class="analise-item">
            <div class="analise-item-title">Média Mensal de Dias</div>
            <div class="analise-item-value">${mediaMensalDias.toFixed(1)}</div>
            <div class="analise-item-desc">Média de dias perdidos por mês</div>
        </div>
        <div class="analise-item">
            <div class="analise-item-title">Mês com Maior Absenteísmo</div>
            <div class="analise-item-value">${mesMaior ? nomesMeses[mesMaior] : 'N/A'}</div>
            <div class="analise-item-desc">${mesMaior ? maiorDias.toFixed(1) + ' dias perdidos' : ''}</div>
        </div>
        <div class="analise-item">
            <div class="analise-item-title">Tendência do Ano</div>
            <div class="analise-item-value">${tendencia}</div>
            <div class="analise-item-desc">${variacao > 0 ? '+' : ''}${variacao}% (2ª metade vs 1ª metade)</div>
        </div>
    `;
}

// Fechar visualização de tendência
function fecharTendencia() {
    const tendenciaDiv = document.getElementById('tendenciaAnual');
    if (tendenciaDiv) {
        tendenciaDiv.classList.remove('show');
    }
    
    // Limpa seleção de ano se não houver mês selecionado
    if (!mesSelecionado) {
        const anoSelect = document.getElementById('anoSelect');
        if (anoSelect) anoSelect.value = '';
        anoSelecionado = null;
    }
}

// Configurar eventos
function setupEventListeners() {
    // Busca global
    document.getElementById('searchBox').addEventListener('input', (e) => {
        searchData(e.target.value);
    });
    
    // Navegação por teclado
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return;
        
        const activeCell = document.querySelector('.cell-focused');
        if (!activeCell) return;
        
        switch(e.key) {
            case 'ArrowRight':
                e.preventDefault();
                navigateToNextCell(activeCell);
                break;
            case 'ArrowLeft':
                e.preventDefault();
                navigateToPreviousCell(activeCell);
                break;
            case 'ArrowDown':
                e.preventDefault();
                navigateToNextRow(activeCell);
                break;
            case 'ArrowUp':
                e.preventDefault();
                navigateToPreviousRow(activeCell);
                break;
            case 'Enter':
                e.preventDefault();
                if (activeCell.classList.contains('editable')) {
                    editCell(activeCell);
                }
                break;
            case 'Home':
                e.preventDefault();
                navigateToFirstCell();
                break;
            case 'End':
                e.preventDefault();
                navigateToLastCell();
                break;
        }
    });
    
    // Clique para focar célula
    document.addEventListener('click', (e) => {
        if (e.target.tagName === 'TD') {
            focusCell(e.target);
        }
    });
}

// Renderizar tabela
function renderTable() {
    const thead = document.getElementById('tableHead');
    const tbody = document.getElementById('tableBody');
    
    // Renderiza cabeçalho dinamicamente
    if (todasColunas.length > 0) {
        thead.innerHTML = `
            <tr>
                ${todasColunas.map(col => `<th>${formatColumnName(col)}</th>`).join('')}
            </tr>
        `;
    } else {
        // Fallback para colunas padrão se não tiver detectado
        thead.innerHTML = `
            <tr>
                <th>ID</th>
                <th>Funcionário</th>
                <th>CPF</th>
                <th>Setor</th>
                <th>Gênero</th>
                <th>Data Afastamento</th>
                <th>Data Retorno</th>
                <th>Tipo</th>
                <th>CID</th>
                <th>Descrição CID</th>
                <th>Dias</th>
                <th>Horas</th>
            </tr>
        `;
    }
    
    if (filteredData.length === 0) {
        const colspan = todasColunas.length || 12;
        tbody.innerHTML = `
            <tr>
                <td colspan="${colspan}" style="text-align: center; padding: 40px;">
                    <i class="fas fa-inbox"></i> Nenhum registro encontrado
                </td>
            </tr>
        `;
        return;
    }
    
    // Renderiza linhas dinamicamente
    tbody.innerHTML = filteredData.map(row => {
        const cells = todasColunas.map(col => {
            const value = row[col];
            const formattedValue = formatCellValue(value, col);
            
            // Define quais campos são editáveis (campos principais da planilha)
            const editableFields = ['nomecompleto', 'descricao_atestad', 'cid', 'diagnostico', 
                                   'centro_custo', 'setor', 'motivo_atestado', 'escala'];
            const isEditable = editableFields.includes(col.toLowerCase());
            
            if (isEditable) {
                return `<td class="editable" data-field="${col}" data-id="${row.id}">${formattedValue}</td>`;
            } else {
                return `<td>${formattedValue}</td>`;
            }
        }).join('');
        
        return `<tr>${cells}</tr>`;
    }).join('');
    
    // Foca na primeira célula editável
    setTimeout(() => {
        const firstEditable = document.querySelector('td.editable');
        if (firstEditable) {
            focusCell(firstEditable);
        }
    }, 100);
}

// Formata nome da coluna para exibição
function formatColumnName(colName) {
    // Mapeamento de nomes técnicos para nomes COMPLETOS EM MAIÚSCULO (planilha padronizada)
    const nomeMap = {
        'nomecompleto': 'NOMECOMPLETO',
        'descricao_atestad': 'DESCRIÇÃO ATESTAD',
        'dias_atestados': 'DIAS ATESTADOS',
        'cid': 'CID',
        'diagnostico': 'DIAGNÓSTICO',
        'centro_custo': 'CENTROCUST',
        'setor': 'SETOR',
        'motivo_atestado': 'MOTIVO ATESTADO',
        'escala': 'ESCALA',
        'horas_dia': 'HORAS/DIA',
        'horas_perdi': 'HORAS PERDI',
        // Campos legados
        'id': 'ID',
        'nome_funcionario': 'NOME FUNCIONÁRIO',
        'cpf': 'CPF',
        'genero': 'GÊNERO',
        'data_afastamento': 'DATA AFASTAMENTO',
        'data_retorno': 'DATA RETORNO',
        'tipo_info_atestado': 'TIPO INFO ATESTADO',
        'tipo_atestado': 'TIPO ATESTADO',
        'descricao_cid': 'DESCRIÇÃO CID',
        'numero_dias_atestado': 'NUMERO DIAS ATESTADO',
        'numero_horas_atestado': 'NUMERO HORAS ATESTADO',
        'dias_perdidos': 'DIAS PERDIDOS',
        'horas_perdidas': 'HORAS PERDIDAS',
        'matricula': 'MATRÍCULA',
        'cargo': 'CARGO'
    };
    
    // Se tiver mapeamento, usa ele
    if (nomeMap[colName.toLowerCase()]) {
        return nomeMap[colName.toLowerCase()];
    }
    
    // Senão, formata o nome da coluna em MAIÚSCULO (remove underscores, converte para maiúsculo)
    return colName
        .replace(/_/g, ' ')
        .toUpperCase();
}

// Formata valor da célula
function formatCellValue(value, colName) {
    if (value === null || value === undefined || value === '') {
        return '-';
    }
    
    const col = colName.toLowerCase();
    
    // Formatação específica por tipo de coluna
    if (col === 'cpf') {
        return formatCPF(value);
    }
    
    if (col.includes('data') || col.includes('datahora') || col.includes('dataemissao')) {
        return formatDate(value);
    }
    
    if (col === 'tipo_info_atestado') {
        return formatTipo(value);
    }
    
    // Para valores numéricos
    if (typeof value === 'number') {
        return value.toLocaleString('pt-BR');
    }
    
    return String(value);
}

// Focar célula
function focusCell(cell) {
    document.querySelectorAll('.cell-focused').forEach(c => {
        c.classList.remove('cell-focused');
    });
    cell.classList.add('cell-focused');
}

// Navegação
function navigateToNextCell(currentCell) {
    const nextCell = currentCell.nextElementSibling;
    if (nextCell) {
        focusCell(nextCell);
        scrollToCell(nextCell);
    } else {
        const nextRow = currentCell.parentElement.nextElementSibling;
        if (nextRow) {
            const firstCell = nextRow.querySelector('td');
            if (firstCell) {
                focusCell(firstCell);
                scrollToCell(firstCell);
            }
        }
    }
}

function navigateToPreviousCell(currentCell) {
    const prevCell = currentCell.previousElementSibling;
    if (prevCell) {
        focusCell(prevCell);
        scrollToCell(prevCell);
    } else {
        const prevRow = currentCell.parentElement.previousElementSibling;
        if (prevRow) {
            const lastCell = prevRow.querySelector('td:last-child');
            if (lastCell) {
                focusCell(lastCell);
                scrollToCell(lastCell);
            }
        }
    }
}

function navigateToNextRow(currentCell) {
    const currentRow = currentCell.parentElement;
    const nextRow = currentRow.nextElementSibling;
    if (nextRow) {
        const cellIndex = Array.from(currentRow.children).indexOf(currentCell);
        const nextCell = nextRow.children[cellIndex];
        if (nextCell) {
            focusCell(nextCell);
            scrollToCell(nextCell);
        }
    }
}

function navigateToPreviousRow(currentCell) {
    const currentRow = currentCell.parentElement;
    const prevRow = currentRow.previousElementSibling;
    if (prevRow) {
        const cellIndex = Array.from(currentRow.children).indexOf(currentCell);
        const prevCell = prevRow.children[cellIndex];
        if (prevCell) {
            focusCell(prevCell);
            scrollToCell(prevCell);
        }
    }
}

// Função para rolar até a célula
function scrollToCell(cell) {
    const tableContainer = document.querySelector('.table-container');
    const cellRect = cell.getBoundingClientRect();
    const containerRect = tableContainer.getBoundingClientRect();
    
    // Scroll horizontal
    if (cellRect.left < containerRect.left) {
        tableContainer.scrollLeft -= (containerRect.left - cellRect.left + 20);
    } else if (cellRect.right > containerRect.right) {
        tableContainer.scrollLeft += (cellRect.right - containerRect.right + 20);
    }
    
    // Scroll vertical
    if (cellRect.top < containerRect.top) {
        tableContainer.scrollTop -= (containerRect.top - cellRect.top + 20);
    } else if (cellRect.bottom > containerRect.bottom) {
        tableContainer.scrollTop += (cellRect.bottom - containerRect.bottom + 20);
    }
}

// Navegar para primeira célula
function navigateToFirstCell() {
    const firstCell = document.querySelector('td');
    if (firstCell) {
        focusCell(firstCell);
        scrollToCell(firstCell);
    }
}

// Navegar para última célula
function navigateToLastCell() {
    const lastCell = document.querySelector('td:last-child');
    if (lastCell) {
        focusCell(lastCell);
        scrollToCell(lastCell);
    }
}

// Editar célula
function editCell(cell) {
    const field = cell.dataset.field;
    const id = cell.dataset.id;
    const currentValue = cell.textContent.trim();
    
    cell.innerHTML = `<input type="text" value="${currentValue}" onblur="saveCell(this, '${field}', ${id})" onkeypress="if(event.key==='Enter') this.blur()">`;
    
    const input = cell.querySelector('input');
    input.focus();
    input.select();
}

// Salvar célula
async function saveCell(input, field, id) {
    const newValue = input.value;
    const cell = input.parentElement;
    
    try {
        const response = await fetch(`/api/dados/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [field]: newValue })
        });
        
        if (response.ok) {
            // Atualiza localmente
            const row = allData.find(r => r.id === id);
            if (row) row[field] = newValue;
            
            cell.textContent = formatValue(newValue, field);
            cell.style.background = '#d4edda';
            setTimeout(() => { cell.style.background = ''; }, 1000);
            
            // Reaplica filtros
            applyFilters();
        } else {
            alert('Erro ao salvar');
            cell.textContent = formatValue(allData.find(r => r.id === id)[field], field);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar');
    }
}

// Buscar dados
function searchData(term) {
    if (!term) {
        filteredData = [...allData];
    } else {
        filteredData = allData.filter(row => {
            return Object.values(row).some(val => {
                if (val === null || val === undefined) return false;
                return String(val).toLowerCase().includes(term.toLowerCase());
            });
        });
    }
    
    updateStats();
    renderTable();
}

// Limpar filtros
function clearFilters() {
    document.getElementById('searchBox').value = '';
    activeFilters = {};
    
    // Limpa seletores de período
    const anoSelect = document.getElementById('anoSelect');
    const mesSelect = document.getElementById('mesSelect');
    if (anoSelect) anoSelect.value = '';
    if (mesSelect) mesSelect.value = '';
    
    anoSelecionado = null;
    mesSelecionado = null;
    
    // Remove destaque das abas
    document.querySelectorAll('.mes-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Fecha tendência anual se estiver aberta
    fecharTendencia();
    
    filteredData = [...allData];
    updateStats();
    renderTable();
}

// Atualizar estatísticas
function updateStats() {
    document.getElementById('totalRecords').textContent = allData.length.toLocaleString('pt-BR');
    document.getElementById('filteredRecords').textContent = filteredData.length.toLocaleString('pt-BR');
    document.getElementById('activeFilters').textContent = Object.keys(activeFilters).length;
}

// Aplicar filtros
function applyFilters() {
    filteredData = allData.filter(row => {
        for (let [field, values] of Object.entries(activeFilters)) {
            if (values.length === 0) continue;
            
            let rowVal = row[field];
            if (rowVal === null || rowVal === undefined || rowVal === '') {
                rowVal = '(Vazio)';
            } else {
                rowVal = String(rowVal);
            }
            
            if (!values.includes(rowVal)) {
                return false;
            }
        }
        return true;
    });
    
    updateStats();
    renderTable();
}

// Exportar dados
function exportData() {
    // Exporta todas as colunas da planilha original
    const data = filteredData.map(row => {
        const exportRow = {};
        todasColunas.forEach(col => {
            exportRow[formatColumnName(col)] = row[col] || '';
        });
        return exportRow;
    });
    
    const csv = convertToCSV(data);
    downloadCSV(csv, 'dados_atestados.csv');
}

// Função melhorada para detectar gênero
function detectarGenero(nome) {
    if (!nome || typeof nome !== 'string') return 'Indefinido';
    
    const nomeLimpo = nome.toLowerCase().trim();
    
    // Nomes femininos comuns no Brasil
    const nomesFemininos = [
        'ana', 'maria', 'joana', 'carla', 'patricia', 'sandra', 'lucia', 'rita', 'rosa', 'elena',
        'fernanda', 'juliana', 'camila', 'bruna', 'leticia', 'vanessa', 'daniela', 'cristina',
        'adriana', 'silvia', 'monica', 'fabiana', 'alessandra', 'andrea', 'claudia', 'denise',
        'eliane', 'fatima', 'gabriela', 'helena', 'isabel', 'jessica', 'karen', 'luciana',
        'marcia', 'natalia', 'olivia', 'paula', 'quenia', 'renata', 'sabrina', 'tatiana',
        'ursula', 'vera', 'wanda', 'yara', 'zilda', 'beatriz', 'carolina', 'diana', 'elisa',
        'flavia', 'gisele', 'hilda', 'iris', 'julia', 'kelly', 'laura', 'marta', 'nina',
        'otilia', 'priscila', 'raquel', 'sara', 'teresa', 'valeria', 'wilma', 'yasmin'
    ];
    
    // Nomes masculinos comuns no Brasil
    const nomesMasculinos = [
        'joao', 'jose', 'antonio', 'francisco', 'carlos', 'paulo', 'pedro', 'lucas', 'luiz',
        'marcos', 'luis', 'gabriel', 'rafael', 'daniel', 'marcelo', 'bruno', 'eduardo',
        'felipe', 'ricardo', 'roberto', 'fernando', 'thiago', 'joaquim', 'guilherme', 'gustavo',
        'rodrigo', 'sergio', 'fabio', 'andre', 'alexandre', 'leonardo', 'vinicius', 'diego',
        'miguel', 'arthur', 'bernardo', 'heitor', 'davi', 'lorenzo', 'theo', 'noah', 'benjamin',
        'samuel', 'enzo', 'joaquim', 'murilo', 'matheus', 'isaac', 'anthony', 'ryan', 'bryan',
        'caio', 'enzo', 'levi', 'henrique', 'lucca', 'nicolas', 'joao miguel', 'pedro henrique',
        'cauã', 'bento', 'antonio', 'vitor', 'emanuel', 'davi lucca', 'benicio', 'augusto',
        'joão gabriel', 'pietro', 'cauê', 'enzo gabriel', 'joão pedro', 'theo', 'anthony gabriel'
    ];
    
    // Primeiro nome (antes do espaço)
    const primeiroNome = nomeLimpo.split(' ')[0];
    
    // Verifica se é nome feminino conhecido
    if (nomesFemininos.includes(primeiroNome)) {
        return 'Feminino';
    }
    
    // Verifica se é nome masculino conhecido
    if (nomesMasculinos.includes(primeiroNome)) {
        return 'Masculino';
    }
    
    // Regras por terminação (mais confiável)
    const terminacoesFemininas = ['a', 'ia', 'ina', 'ana', 'ena', 'ela', 'ila', 'ola', 'ula'];
    const terminacoesMasculinas = ['o', 'io', 'ao', 'eo', 'uo', 'os', 'us', 'es', 'is'];
    
    // Verifica terminação feminina
    for (const term of terminacoesFemininas) {
        if (primeiroNome.endsWith(term)) {
            return 'Feminino';
        }
    }
    
    // Verifica terminação masculina
    for (const term of terminacoesMasculinas) {
        if (primeiroNome.endsWith(term)) {
            return 'Masculino';
        }
    }
    
    // Se não conseguiu determinar, retorna indefinido
    return 'Indefinido';
}

// Detectar gêneros automaticamente
async function detectarGeneros() {
    const botao = document.querySelector('button[onclick="detectarGeneros()"]');
    const textoOriginal = botao.innerHTML;
    
    botao.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detectando...';
    botao.disabled = true;
    
    let atualizados = 0;
    let erros = 0;
    
    for (let i = 0; i < allData.length; i++) {
        const registro = allData[i];
        const nome = registro.nome_funcionario;
        
        if (nome && (!registro.genero || registro.genero === 'Indefinido')) {
            const generoDetectado = detectarGenero(nome);
            
            if (generoDetectado !== 'Indefinido') {
                try {
                    const response = await fetch(`/api/dados/${registro.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ genero: generoDetectado })
                    });
                    
                    if (response.ok) {
                        registro.genero = generoDetectado;
                        atualizados++;
                    } else {
                        erros++;
                    }
                } catch (error) {
                    erros++;
                }
            }
        }
        
        // Atualiza progresso a cada 10 registros
        if (i % 10 === 0) {
            botao.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Detectando... ${i}/${allData.length}`;
        }
    }
    
    // Reaplica filtros e atualiza tabela
    applyFilters();
    
    // Restaura botão
    botao.innerHTML = textoOriginal;
    botao.disabled = false;
    
    // Mostra resultado
    alert(`✅ Detecção concluída!\n\n📊 Resultados:\n• ${atualizados} gêneros detectados\n• ${erros} erros\n• ${allData.length - atualizados - erros} já tinham gênero definido`);
}

// Funções auxiliares
function formatCPF(cpf) {
    if (!cpf) return '';
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

function formatDate(date) {
    if (!date) return '';
    return new Date(date).toLocaleDateString('pt-BR');
}

function formatTipo(tipo) {
    if (tipo === 1) return 'Dias';
    if (tipo === 3) return 'Horas';
    return '';
}

function formatValue(value, field) {
    if (field === 'cpf') return formatCPF(value);
    if (field === 'data_afastamento' || field === 'data_retorno') return formatDate(value);
    return value || '-';
}

function convertToCSV(data) {
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n');
    
    return csvContent;
}

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function showError(message) {
    const tbody = document.getElementById('tableBody');
    const colspan = todasColunas.length || 12;
    tbody.innerHTML = `
        <tr>
            <td colspan="${colspan}" style="text-align: center; padding: 40px; color: #dc3545;">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </td>
        </tr>
    `;
}
