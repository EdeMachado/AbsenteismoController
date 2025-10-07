// Dashboard PowerBI - JavaScript
let powerbiCharts = {};
let powerbiData = [];
let powerbiFilters = {};

// Cores PowerBI
const POWERBI_COLORS = [
    '#00bcf2', '#ff6b6b', '#4ecdc4', '#45b7d1', 
    '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff',
    '#5f27cd', '#00d2d3', '#ff9f43', '#10ac84'
];

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Iniciando Dashboard PowerBI...');
    
    // Carrega dados
    await loadPowerbiData();
    
    // Inicializa filtros
    initializeFilters();
    
    // Cria gráficos
    createAllCharts();
    
    // Atualiza estatísticas
    updateStats();
    
    console.log('✅ Dashboard PowerBI carregado!');
});

// ==================== CARREGAMENTO DE DADOS ====================

async function loadPowerbiData() {
    try {
        console.log('📊 Carregando dados...');
        
        const response = await fetch('/api/dados/todos?client_id=1');
        const data = await response.json();
        
        powerbiData = data;
        console.log(`✅ ${powerbiData.length} registros carregados`);
        
    } catch (error) {
        console.error('❌ Erro ao carregar dados:', error);
        powerbiData = [];
    }
}

// ==================== INICIALIZAÇÃO DE FILTROS ====================

function initializeFilters() {
    console.log('🔧 Inicializando filtros...');
    
    // Extrai valores únicos para filtros
    const departamentos = [...new Set(powerbiData.map(d => d.setor).filter(Boolean))];
    const funcionarios = [...new Set(powerbiData.map(d => d.nome_funcionario).filter(Boolean))];
    const tiposDoenca = [...new Set(powerbiData.map(d => d.descricao_cid).filter(Boolean))];
    const anos = [...new Set(powerbiData.map(d => {
        if (d.data_afastamento) {
            return new Date(d.data_afastamento).getFullYear();
        }
        return null;
    }).filter(Boolean))].sort();
    
    const meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];
    
    // Preenche dropdowns
    populateDropdown('filterDepartamento', departamentos);
    populateDropdown('filterFuncionario', funcionarios);
    populateDropdown('filterTipoDoenca', tiposDoenca);
    populateDropdown('filterAno', anos);
    populateDropdown('filterMes', meses);
    
    // Adiciona event listeners
    document.querySelectorAll('.filter-dropdown').forEach(dropdown => {
        dropdown.addEventListener('change', applyFilters);
    });
    
    console.log('✅ Filtros inicializados');
}

function populateDropdown(id, options) {
    const dropdown = document.getElementById(id);
    if (!dropdown) return;
    
    // Limpa opções existentes (exceto "Todos")
    dropdown.innerHTML = '<option value="">Todos</option>';
    
    // Adiciona novas opções
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        dropdown.appendChild(optionElement);
    });
}

// ==================== APLICAÇÃO DE FILTROS ====================

function applyFilters() {
    console.log('🔍 Aplicando filtros...');
    
    // Coleta valores dos filtros
    powerbiFilters = {
        departamento: document.getElementById('filterDepartamento').value,
        funcionario: document.getElementById('filterFuncionario').value,
        tipoDoenca: document.getElementById('filterTipoDoenca').value,
        ano: document.getElementById('filterAno').value,
        mes: document.getElementById('filterMes').value,
        procedencia: document.getElementById('filterProcedencia').value
    };
    
    // Filtra dados
    let filteredData = powerbiData.filter(record => {
        if (powerbiFilters.departamento && record.setor !== powerbiFilters.departamento) return false;
        if (powerbiFilters.funcionario && record.nome_funcionario !== powerbiFilters.funcionario) return false;
        if (powerbiFilters.tipoDoenca && record.descricao_cid !== powerbiFilters.tipoDoenca) return false;
        if (powerbiFilters.ano) {
            const recordYear = new Date(record.data_afastamento).getFullYear();
            if (recordYear.toString() !== powerbiFilters.ano) return false;
        }
        if (powerbiFilters.mes) {
            const recordMonth = new Date(record.data_afastamento).getMonth() + 1;
            const filterMonth = meses.indexOf(powerbiFilters.mes) + 1;
            if (recordMonth !== filterMonth) return false;
        }
        return true;
    });
    
    console.log(`📊 Dados filtrados: ${filteredData.length} registros`);
    
    // Atualiza gráficos com dados filtrados
    updateAllCharts(filteredData);
    updateStats(filteredData);
}

// ==================== CRIAÇÃO DE GRÁFICOS ====================

function createAllCharts() {
    console.log('📈 Criando gráficos...');
    
    createChartFuncionarios();
    createChartSetores();
    createChartAnos();
    createChartDoencas();
    createChartAnalise();
    createChartTempoServico();
    
    console.log('✅ Todos os gráficos criados');
}

function createChartFuncionarios() {
    const ctx = document.getElementById('chartFuncionarios').getContext('2d');
    
    // Agrupa por funcionário
    const funcionariosData = {};
    powerbiData.forEach(record => {
        if (record.nome_funcionario) {
            if (!funcionariosData[record.nome_funcionario]) {
                funcionariosData[record.nome_funcionario] = {
                    dias: 0,
                    horas: 0,
                    registros: 0
                };
            }
            funcionariosData[record.nome_funcionario].dias += record.dias_atestado || 0;
            funcionariosData[record.nome_funcionario].horas += record.horas_atestado || 0;
            funcionariosData[record.nome_funcionario].registros += 1;
        }
    });
    
    // Ordena por dias e pega top 10
    const topFuncionarios = Object.entries(funcionariosData)
        .sort(([,a], [,b]) => b.dias - a.dias)
        .slice(0, 10);
    
    powerbiCharts.funcionarios = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topFuncionarios.map(([nome]) => nome.split(' ')[0]), // Primeiro nome
            datasets: [{
                label: 'Dias de Atestado',
                data: topFuncionarios.map(([,data]) => data.dias),
                backgroundColor: POWERBI_COLORS[0],
                borderColor: POWERBI_COLORS[0],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f0f0f0'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function createChartSetores() {
    const ctx = document.getElementById('chartSetores').getContext('2d');
    
    // Agrupa por setor
    const setoresData = {};
    powerbiData.forEach(record => {
        if (record.setor) {
            if (!setoresData[record.setor]) {
                setoresData[record.setor] = 0;
            }
            setoresData[record.setor] += record.dias_atestado || 0;
        }
    });
    
    powerbiCharts.setores = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(setoresData),
            datasets: [{
                data: Object.values(setoresData),
                backgroundColor: POWERBI_COLORS.slice(0, Object.keys(setoresData).length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

function createChartAnos() {
    const ctx = document.getElementById('chartAnos').getContext('2d');
    
    // Agrupa por ano
    const anosData = {};
    powerbiData.forEach(record => {
        if (record.data_afastamento) {
            const ano = new Date(record.data_afastamento).getFullYear();
            if (!anosData[ano]) {
                anosData[ano] = 0;
            }
            anosData[ano] += record.dias_atestado || 0;
        }
    });
    
    const anosOrdenados = Object.keys(anosData).sort();
    
    powerbiCharts.anos = new Chart(ctx, {
        type: 'line',
        data: {
            labels: anosOrdenados,
            datasets: [{
                label: 'Dias de Atestado',
                data: anosOrdenados.map(ano => anosData[ano]),
                borderColor: POWERBI_COLORS[1],
                backgroundColor: POWERBI_COLORS[1] + '20',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f0f0f0'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function createChartDoencas() {
    const ctx = document.getElementById('chartDoencas').getContext('2d');
    
    // Agrupa por CID
    const doencasData = {};
    powerbiData.forEach(record => {
        if (record.cid) {
            if (!doencasData[record.cid]) {
                doencasData[record.cid] = {
                    count: 0,
                    dias: 0
                };
            }
            doencasData[record.cid].count += 1;
            doencasData[record.cid].dias += record.dias_atestado || 0;
        }
    });
    
    // Top 8 doenças
    const topDoencas = Object.entries(doencasData)
        .sort(([,a], [,b]) => b.count - a.count)
        .slice(0, 8);
    
    powerbiCharts.doencas = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topDoencas.map(([cid]) => cid),
            datasets: [{
                label: 'Ocorrências',
                data: topDoencas.map(([,data]) => data.count),
                backgroundColor: POWERBI_COLORS[2],
                borderColor: POWERBI_COLORS[2],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f0f0f0'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function createChartAnalise() {
    const ctx = document.getElementById('chartAnalise').getContext('2d');
    
    // Análise por tipo de atestado (simulado)
    const analiseData = {
        'Atestado Médico': 45,
        'Licença Maternidade': 12,
        'Afastamento': 8,
        'Outros': 5
    };
    
    powerbiCharts.analise = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(analiseData),
            datasets: [{
                data: Object.values(analiseData),
                backgroundColor: POWERBI_COLORS.slice(0, 4),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

function createChartTempoServico() {
    const ctx = document.getElementById('chartTempoServico').getContext('2d');
    
    // Simula dados de tempo de serviço vs atestados
    const tempoServicoData = {
        '0-2 anos': 15,
        '2-5 anos': 25,
        '5-10 anos': 35,
        '10-15 anos': 20,
        '15+ anos': 5
    };
    
    powerbiCharts.tempoServico = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(tempoServicoData),
            datasets: [{
                label: 'Dias de Atestado',
                data: Object.values(tempoServicoData),
                backgroundColor: POWERBI_COLORS[3],
                borderColor: POWERBI_COLORS[3],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f0f0f0'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ==================== ATUALIZAÇÃO DE GRÁFICOS ====================

function updateAllCharts(filteredData = powerbiData) {
    console.log('🔄 Atualizando gráficos...');
    
    updateChartFuncionarios(filteredData);
    updateChartSetores(filteredData);
    updateChartAnos(filteredData);
    updateChartDoencas(filteredData);
    
    console.log('✅ Gráficos atualizados');
}

function updateChartFuncionarios(data) {
    if (!powerbiCharts.funcionarios) return;
    
    const funcionariosData = {};
    data.forEach(record => {
        if (record.nome_funcionario) {
            if (!funcionariosData[record.nome_funcionario]) {
                funcionariosData[record.nome_funcionario] = 0;
            }
            funcionariosData[record.nome_funcionario] += record.dias_atestado || 0;
        }
    });
    
    const topFuncionarios = Object.entries(funcionariosData)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10);
    
    powerbiCharts.funcionarios.data.labels = topFuncionarios.map(([nome]) => nome.split(' ')[0]);
    powerbiCharts.funcionarios.data.datasets[0].data = topFuncionarios.map(([,dias]) => dias);
    powerbiCharts.funcionarios.update();
}

function updateChartSetores(data) {
    if (!powerbiCharts.setores) return;
    
    const setoresData = {};
    data.forEach(record => {
        if (record.setor) {
            if (!setoresData[record.setor]) {
                setoresData[record.setor] = 0;
            }
            setoresData[record.setor] += record.dias_atestado || 0;
        }
    });
    
    powerbiCharts.setores.data.labels = Object.keys(setoresData);
    powerbiCharts.setores.data.datasets[0].data = Object.values(setoresData);
    powerbiCharts.setores.data.datasets[0].backgroundColor = POWERBI_COLORS.slice(0, Object.keys(setoresData).length);
    powerbiCharts.setores.update();
}

function updateChartAnos(data) {
    if (!powerbiCharts.anos) return;
    
    const anosData = {};
    data.forEach(record => {
        if (record.data_afastamento) {
            const ano = new Date(record.data_afastamento).getFullYear();
            if (!anosData[ano]) {
                anosData[ano] = 0;
            }
            anosData[ano] += record.dias_atestado || 0;
        }
    });
    
    const anosOrdenados = Object.keys(anosData).sort();
    
    powerbiCharts.anos.data.labels = anosOrdenados;
    powerbiCharts.anos.data.datasets[0].data = anosOrdenados.map(ano => anosData[ano]);
    powerbiCharts.anos.update();
}

function updateChartDoencas(data) {
    if (!powerbiCharts.doencas) return;
    
    const doencasData = {};
    data.forEach(record => {
        if (record.cid) {
            if (!doencasData[record.cid]) {
                doencasData[record.cid] = 0;
            }
            doencasData[record.cid] += 1;
        }
    });
    
    const topDoencas = Object.entries(doencasData)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 8);
    
    powerbiCharts.doencas.data.labels = topDoencas.map(([cid]) => cid);
    powerbiCharts.doencas.data.datasets[0].data = topDoencas.map(([,count]) => count);
    powerbiCharts.doencas.update();
}

// ==================== ATUALIZAÇÃO DE ESTATÍSTICAS ====================

function updateStats(data = powerbiData) {
    console.log('📊 Atualizando estatísticas...');
    
    const totalRegistros = data.length;
    const totalDias = data.reduce((sum, record) => sum + (record.dias_atestado || 0), 0);
    const totalHoras = data.reduce((sum, record) => sum + (record.horas_atestado || 0), 0);
    
    // Taxa de absenteísmo (simulada)
    const taxaAbsenteismo = totalRegistros > 0 ? ((totalDias / (totalRegistros * 30)) * 100).toFixed(1) : 0;
    
    // Atualiza elementos
    document.getElementById('totalRegistros').textContent = totalRegistros.toLocaleString();
    document.getElementById('totalDias').textContent = totalDias.toLocaleString();
    document.getElementById('totalHoras').textContent = totalHoras.toLocaleString();
    document.getElementById('taxaAbsenteismo').textContent = taxaAbsenteismo + '%';
    
    console.log('✅ Estatísticas atualizadas');
}

// ==================== FUNÇÕES DE INTERFACE ====================

function showTab(tabName) {
    // Remove active de todas as abas
    document.querySelectorAll('.tool-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Esconde todo conteúdo
    document.querySelectorAll('[id^="tab-"]').forEach(content => {
        content.style.display = 'none';
    });
    
    // Ativa aba selecionada
    event.target.classList.add('active');
    document.getElementById(`tab-${tabName}`).style.display = 'block';
}

function addChart(type) {
    console.log(`➕ Adicionando gráfico ${type}`);
    
    // Aqui você pode implementar a lógica para adicionar novos gráficos
    // Por enquanto, apenas mostra uma mensagem
    alert(`Gráfico ${type} será adicionado em breve!`);
}

// ==================== UTILITÁRIOS ====================

function exportToExcel() {
    console.log('📤 Exportando para Excel...');
    
    // Implementar exportação para Excel
    alert('Exportação para Excel será implementada em breve!');
}

function exportToPDF() {
    console.log('📄 Exportando para PDF...');
    
    // Implementar exportação para PDF
    alert('Exportação para PDF será implementada em breve!');
}

// ==================== INICIALIZAÇÃO FINAL ====================

console.log('🎯 Dashboard PowerBI carregado e pronto!');
