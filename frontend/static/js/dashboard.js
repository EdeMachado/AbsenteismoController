// ==================== VARIÁVEIS GLOBAIS ====================
// Paleta de Cores da Empresa (Azul Marinho e Verde Oliva)
const CORES_EMPRESA = {
    primary: '#1a237e',        // Azul Marinho principal
    primaryDark: '#0d47a1',    // Azul Marinho escuro
    primaryLight: '#3949ab',   // Azul Marinho claro
    primaryLighter: '#5c6bc0', // Azul Marinho mais claro
    primaryDarkest: '#000051', // Azul Marinho muito escuro
    secondary: '#556B2F',      // Verde Oliva principal
    secondaryDark: '#4a5d23',  // Verde Oliva escuro
    secondaryLight: '#6B8E23', // Verde Oliva claro
    secondaryLighter: '#808000',// Verde Oliva mais claro
    gray: '#9E9E9E',           // Cinza
    grayLight: '#BDBDBD',      // Cinza claro
    grayDark: '#757575',       // Cinza escuro
    masculino: '#1a237e',      // Azul Marinho
    feminino: '#556B2F'        // Verde Oliva
};

const PALETA_EMPRESA = [
    '#1a237e',  // Azul Marinho principal
    '#556B2F',  // Verde Oliva principal
    '#0d47a1',  // Azul Marinho escuro
    '#6B8E23',  // Verde Oliva claro
    '#3949ab',  // Azul Marinho claro
    '#808000',  // Verde Oliva mais claro
    '#5c6bc0',  // Azul Marinho mais claro
    '#4a5d23',  // Verde Oliva escuro
    '#9E9E9E',  // Cinza
    '#757575'   // Cinza escuro
];

let chartCids = null;
let chartSetores = null;
let chartEvolucao = null;
let chartGenero = null;
let chartMediaCid = null;
let chartFuncionariosDias = null;
let chartEscalas = null;
let chartMotivos = null;
let chartCentroCusto = null;
let chartDistribuicaoDias = null;
let chartMediaCidDias = null;
let chartEvolucaoSetor = null;
let chartComparativoDiasHoras = null;
let chartFrequenciaAtestados = null;
let chartSetorGenero = null;
let chartProdutividade = null;
let chartProdutividadeEvolucao = null;
let chartProdutividadeMensalCategoria = null;

const getClientId = () => (typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null);

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', async () => {
    await carregarFiltros();
    carregarDashboard();
});

// ==================== CARREGAR DASHBOARD ====================
async function carregarDashboard() {
    try {
        const clientId = getClientId();
        if (!clientId) {
            alert('Selecione um cliente na aba "Clientes" para visualizar o dashboard.');
            return;
        }

        // Pega valores dos filtros (se existirem)
        const mesInicio = document.getElementById('mesInicio')?.value || '';
        const mesFim = document.getElementById('mesFim')?.value || '';
        
        // Pega múltiplos funcionários selecionados (checkboxes)
        const containerFuncionarios = document.getElementById('checkboxesFuncionarios');
        const funcionarios = Array.from(containerFuncionarios?.querySelectorAll('input[type="checkbox"]:checked') || [])
            .map(cb => cb.value)
            .filter(v => v);
        
        // Pega múltiplos setores selecionados (checkboxes)
        const containerSetores = document.getElementById('checkboxesSetores');
        const setores = Array.from(containerSetores?.querySelectorAll('input[type="checkbox"]:checked') || [])
            .map(cb => cb.value)
            .filter(v => v);
        
        let url = `/api/dashboard?client_id=${clientId}`;
        if (mesInicio) url += `&mes_inicio=${encodeURIComponent(mesInicio)}`;
        if (mesFim) url += `&mes_fim=${encodeURIComponent(mesFim)}`;
        
        // Adiciona múltiplos funcionários
        funcionarios.forEach(func => {
            url += `&funcionario=${encodeURIComponent(func)}`;
        });
        
        // Adiciona múltiplos setores
        setores.forEach(setor => {
            url += `&setor=${encodeURIComponent(setor)}`;
        });
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}`);
        }
        
        const data = await response.json();
        
        // Renderiza cards
        renderizarCards(data.metricas || {});
        
        // Armazena alertas para o menu (não renderiza aqui)
        window.alertasData = data.alertas || [];
        if (typeof carregarAlertasMenu === 'function') {
            carregarAlertasMenu();
        }
        
        // Renderiza insights
        renderizarInsights(data.insights || []);
        renderizarChartCids(data.top_cids || []);
        renderizarChartSetores(data.top_setores || []);
        renderizarChartEvolucao(data.evolucao_mensal || []);
        renderizarChartGenero(data.distribuicao_genero || []);
        renderizarChartMediaCid(data.top_cids || []);
        renderizarChartFuncionariosDias(data.top_funcionarios || []);
        renderizarChartEscalas(data.top_escalas || []);
        renderizarChartMotivos(data.top_motivos || []);
        renderizarChartCentroCusto(data.dias_centro_custo || []);
        renderizarChartDistribuicaoDias(data.distribuicao_dias || []);
        renderizarChartMediaCidDias(data.media_cid || []);
        renderizarChartEvolucaoSetor(data.evolucao_setor || {});
        renderizarChartComparativoDiasHoras(data.comparativo_dias_horas || []);
        renderizarChartFrequenciaAtestados(data.frequencia_atestados || []);
        renderizarChartSetorGenero(data.dias_setor_genero || []);
        renderizarChartProdutividade(data.produtividade || []);
        renderizarChartProdutividadeMensalCategoria(data.produtividade || []);
        
        // Carrega evolução de produtividade separadamente
        await carregarEvolucaoProdutividade();
        
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        alert('Erro ao carregar dados. Verifique se o servidor está funcionando.');
    }
}


// ==================== RENDERIZAR CARDS ====================
function renderizarCards(metricas) {
    // Dias Perdidos = Soma da coluna DIAS ATESTADOS
    const diasPerdidos = metricas.total_dias_perdidos || 0;
    const elDiasPerdidos = document.getElementById('cardDiasPerdidos');
    if (elDiasPerdidos) {
        elDiasPerdidos.textContent = Math.round(diasPerdidos).toLocaleString('pt-BR');
    }
    
    // Horas Perdidas = Soma da coluna HORAS PERDI
    const horasPerdidas = metricas.total_horas_perdidas || 0;
    const elHorasPerdidas = document.getElementById('cardHorasPerdidas');
    if (elHorasPerdidas) {
        elHorasPerdidas.textContent = Math.round(horasPerdidas).toLocaleString('pt-BR');
    }
}

// ==================== RENDERIZAR INSIGHTS ====================
function renderizarInsights(insights) {
    const container = document.getElementById('insightsContainer');
    const section = document.getElementById('insightsSection');
    
    if (!insights || insights.length === 0) {
        if (section) section.style.display = 'none';
        return;
    }
    
    if (section) section.style.display = 'block';
    
    if (container) {
        container.innerHTML = insights.map(insight => `
            <div class="insight-card ${insight.tipo}">
                <div class="insight-header">
                    <div class="insight-icon">${insight.icone}</div>
                    <div class="insight-content">
                        <div class="insight-titulo">${insight.titulo}</div>
                        <div class="insight-descricao">${insight.descricao}</div>
                        <div class="insight-recomendacao">
                            <i class="fas fa-lightbulb"></i>
                            ${insight.recomendacao}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

// ==================== GRÁFICOS ====================
function renderizarChartCids(dados) {
    const ctx = document.getElementById('chartCids');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartCids) chartCids.destroy();
    
    chartCids = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dados.map(d => truncate(d.descricao || d.cid, 28)),
            datasets: [{
                label: 'Atestados',
                data: dados.map(d => d.quantidade),
                backgroundColor: CORES_EMPRESA.primary,
                borderRadius: 6,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            const item = dados[index];
                            return `CID ${item.cid || 'N/A'}`;
                        },
                        label: function(context) {
                            const index = context.dataIndex;
                            const item = dados[index];
                            const diagnostico = item.descricao || item.diagnostico || 'Não especificado';
                            return [
                                `Diagnóstico: ${diagnostico}`,
                                `Quantidade: ${item.quantidade || 0} atestados`
                            ];
                        },
                        afterLabel: function(context) {
                            const index = context.dataIndex;
                            const item = dados[index];
                            if (item.dias_perdidos) {
                                return `Dias perdidos: ${item.dias_perdidos}`;
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                x: { beginAtZero: true },
                y: { ticks: { font: { size: 11 } } }
            }
        }
    });
}

function renderizarChartSetores(dados) {
    const ctx = document.getElementById('chartSetores');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartSetores) chartSetores.destroy();
    
    // Pega TOP 5 setores
    const top5 = dados.slice(0, 5);
    
    chartSetores = new Chart(ctx, {
        type: 'line',
        data: {
            labels: top5.map(d => truncate(d.setor, 20)),
            datasets: [{
                label: 'Quantidade de Atestados',
                data: top5.map(d => d.quantidade),
                borderColor: CORES_EMPRESA.primary,
                backgroundColor: 'rgba(26, 35, 126, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: CORES_EMPRESA.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    display: true, 
                    position: 'top',
                    labels: { font: { size: 11 } }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const setor = top5[index];
                            return [
                                `Atestados: ${context.parsed.y}`,
                                `Dias Perdidos: ${setor.dias_perdidos || 0}`,
                                `Horas Perdidas: ${setor.horas_perdidas || 0}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: { 
                    beginAtZero: true,
                    ticks: { 
                        font: { size: 11 },
                        stepSize: 1
                    }
                },
                x: {
                    ticks: { 
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function renderizarChartEvolucao(dados) {
    const ctx = document.getElementById('chartEvolucao');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartEvolucao) chartEvolucao.destroy();
    
    chartEvolucao = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dados.map(d => d.mes),
            datasets: [{
                label: 'Dias Perdidos',
                data: dados.map(d => d.dias_perdidos),
                borderColor: CORES_EMPRESA.primary,
                backgroundColor: 'rgba(26, 35, 126, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'top' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderizarChartGenero(dados) {
    const ctx = document.getElementById('chartGenero');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartGenero) chartGenero.destroy();
    
    chartGenero = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: dados.map(d => d.genero === 'M' ? 'Masculino' : 'Feminino'),
            datasets: [{
                data: dados.map(d => d.quantidade),
                backgroundColor: [CORES_EMPRESA.feminino, CORES_EMPRESA.masculino]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { font: { size: 11 } } }
            }
        }
    });
}

function renderizarChartMediaCid(dados) {
    const ctx = document.getElementById('chartMediaCid');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartMediaCid) chartMediaCid.destroy();
    
    const top5 = dados.slice(0, 5);
    
    chartMediaCid = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top5.map(d => truncate(d.descricao || d.cid, 18)),
            datasets: [{
                label: 'Dias',
                data: top5.map(d => d.dias_perdidos),
                backgroundColor: CORES_EMPRESA.secondary
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// ==================== NOVOS GRÁFICOS ====================

function renderizarChartFuncionariosDias(dados) {
    const ctx = document.getElementById('chartFuncionariosDias');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartFuncionariosDias) chartFuncionariosDias.destroy();
    
    // TOP 10 funcionários ordenados por dias perdidos
    const top10 = dados.slice(0, 10).sort((a, b) => (b.dias_perdidos || 0) - (a.dias_perdidos || 0));
    
    chartFuncionariosDias = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(d => truncate(d.nome, 25)),
            datasets: [{
                label: 'Dias Perdidos',
                data: top10.map(d => d.dias_perdidos || 0),
                backgroundColor: CORES_EMPRESA.primaryDark,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const func = top10[index];
                            return [
                                `Dias Perdidos: ${context.parsed.x}`,
                                `Atestados: ${func.quantidade || 0}`,
                                `Setor: ${func.setor || 'N/A'}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: { beginAtZero: true },
                y: { ticks: { font: { size: 11 } } }
            }
        }
    });
}

function renderizarChartEscalas(dados) {
    const ctx = document.getElementById('chartEscalas');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartEscalas) chartEscalas.destroy();
    
    // TOP 10 escalas
    const top10 = dados.slice(0, 10);
    
    chartEscalas = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(d => d.escala || 'Não informado'),
            datasets: [{
                label: 'Quantidade de Atestados',
                data: top10.map(d => d.quantidade || 0),
                backgroundColor: CORES_EMPRESA.primary,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y', // Muda para horizontal
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const escala = top10[index];
                            return [
                                `Escala: ${escala.escala || 'Não informado'}`,
                                `Atestados: ${context.parsed.x}`,
                                `Dias Perdidos: ${escala.dias_perdidos || 0}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: { 
                    beginAtZero: true,
                    ticks: { font: { size: 11 }, stepSize: 1 }
                },
                y: { 
                    ticks: { 
                        font: { size: 11 },
                        maxRotation: 0,
                        autoSkip: false
                    }
                }
            }
        }
    });
}

function renderizarChartMotivos(dados) {
    const ctx = document.getElementById('chartMotivos');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartMotivos) chartMotivos.destroy();
    
    // TOP 10 motivos
    const top10 = dados.slice(0, 10);
    
    chartMotivos = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: top10.map(d => truncate(d.motivo, 30)),
            datasets: [{
                label: 'Percentual',
                data: top10.map(d => d.percentual || 0),
                backgroundColor: PALETA_EMPRESA
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: 'right',
                    labels: { 
                        font: { size: 11 },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                const total = top10.reduce((sum, m) => sum + (m.quantidade || 0), 0);
                                return data.labels.map((label, i) => {
                                    const dataset = data.datasets[0];
                                    const motivo = top10[i];
                                    const quantidade = motivo.quantidade || 0;
                                    const percentual = total > 0 ? ((quantidade / total) * 100).toFixed(1) : 0;
                                    return {
                                        text: `${label} - ${percentual}% (${quantidade} atestados)`,
                                        fillStyle: dataset.backgroundColor[i],
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const motivo = top10[index];
                            const total = top10.reduce((sum, m) => sum + (m.quantidade || 0), 0);
                            const percentual = total > 0 ? ((motivo.quantidade || 0) / total * 100).toFixed(1) : 0;
                            return [
                                `Motivo: ${motivo.motivo || 'N/A'}`,
                                `Quantidade: ${motivo.quantidade || 0} atestados`,
                                `Percentual: ${percentual}%`
                            ];
                        }
                    }
                }
            }
        }
    });
}

// ==================== NOVOS GRÁFICOS ADICIONAIS ====================

function renderizarChartCentroCusto(dados) {
    const ctx = document.getElementById('chartCentroCusto');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartCentroCusto) chartCentroCusto.destroy();
    
    chartCentroCusto = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dados.map(d => truncate(d.centro_custo, 25)),
            datasets: [{
                label: 'Dias Perdidos',
                data: dados.map(d => d.dias_perdidos || 0),
                backgroundColor: CORES_EMPRESA.primaryDark,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const item = dados[index];
                            return [
                                `Dias Perdidos: ${context.parsed.x}`,
                                `Atestados: ${item.quantidade || 0}`,
                                `Horas Perdidas: ${item.horas_perdidas || 0}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: { beginAtZero: true },
                y: { ticks: { font: { size: 11 } } }
            }
        }
    });
}

function renderizarChartDistribuicaoDias(dados) {
    const ctx = document.getElementById('chartDistribuicaoDias');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartDistribuicaoDias) chartDistribuicaoDias.destroy();
    
    chartDistribuicaoDias = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dados.map(d => d.faixa),
            datasets: [{
                label: 'Quantidade de Atestados',
                data: dados.map(d => d.quantidade),
                backgroundColor: CORES_EMPRESA.primary,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { 
                    beginAtZero: true,
                    ticks: { font: { size: 11 }, stepSize: 1 }
                },
                x: { ticks: { font: { size: 11 } } }
            }
        }
    });
}

function renderizarChartMediaCidDias(dados) {
    const ctx = document.getElementById('chartMediaCidDias');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartMediaCidDias) chartMediaCidDias.destroy();
    
    chartMediaCidDias = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dados.map(d => truncate(d.cid + ' - ' + (d.diagnostico || ''), 30)),
            datasets: [{
                label: 'Média de Dias',
                data: dados.map(d => d.media_dias || 0),
                backgroundColor: CORES_EMPRESA.primary,  // Azul Marinho
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const item = dados[index];
                            return [
                                `Média: ${context.parsed.x} dias`,
                                `Total: ${item.total_dias || 0} dias`,
                                `Atestados: ${item.quantidade || 0}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: { beginAtZero: true },
                y: { ticks: { font: { size: 11 } } }
            }
        }
    });
}

function renderizarChartEvolucaoSetor(dados) {
    const ctx = document.getElementById('chartEvolucaoSetor');
    if (!ctx || !dados || Object.keys(dados).length === 0) return;
    
    if (chartEvolucaoSetor) chartEvolucaoSetor.destroy();
    
    // Pega os setores e calcula total de dias perdidos por setor
    const setoresData = [];
    Object.keys(dados).forEach(setor => {
        if (dados[setor] && Array.isArray(dados[setor])) {
            let totalDias = 0;
            dados[setor].forEach(item => {
                if (item && item.dias_perdidos) {
                    totalDias += item.dias_perdidos || 0;
                }
            });
            if (totalDias > 0) {
                setoresData.push({
                    setor: setor,
                    dias: totalDias
                });
            }
        }
    });
    
    // Ordena por dias perdidos e pega TOP 10
    setoresData.sort((a, b) => b.dias - a.dias);
    const topSetores = setoresData.slice(0, 10);
    
    if (topSetores.length === 0) return;
    
    const cores = PALETA_EMPRESA;
    
    chartEvolucaoSetor = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topSetores.map(s => truncate(s.setor, 25)),
            datasets: [{
                label: 'Dias Perdidos',
                data: topSetores.map(s => s.dias),
                backgroundColor: topSetores.map((s, idx) => cores[idx % cores.length]),
                borderRadius: 6,
                borderWidth: 1,
                borderColor: topSetores.map((s, idx) => cores[idx % cores.length])
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 10,
                    titleFont: { size: 12 },
                    bodyFont: { size: 12 },
                    callbacks: {
                        label: function(context) {
                            return `Dias Perdidos: ${context.parsed.x} dias`;
                        }
                    }
                }
            },
            scales: {
                x: { 
                    beginAtZero: true,
                    ticks: { 
                        font: { size: 11 },
                        stepSize: 1,
                        precision: 0
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        lineWidth: 1
                    },
                    title: {
                        display: true,
                        text: 'Dias Perdidos',
                        font: { size: 12 }
                    }
                },
                y: {
                    ticks: { 
                        font: { size: 11 }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function renderizarChartComparativoDiasHoras(dados) {
    const ctx = document.getElementById('chartComparativoDiasHoras');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartComparativoDiasHoras) chartComparativoDiasHoras.destroy();
    
    // Pega TOP 8 setores
    const top8 = dados.slice(0, 8);
    
    chartComparativoDiasHoras = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top8.map(d => truncate(d.setor, 20)),
            datasets: [
                {
                    label: 'Dias Perdidos',
                    data: top8.map(d => d.dias_perdidos || 0),
                    backgroundColor: CORES_EMPRESA.primary,
                    borderRadius: 6
                },
                {
                    label: 'Horas Perdidas',
                    data: top8.map(d => (d.horas_perdidas || 0) / 8), // Converte horas para dias equivalentes
                    backgroundColor: CORES_EMPRESA.primaryDark,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { font: { size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const item = top8[index];
                            if (context.datasetIndex === 0) {
                                return `Dias Perdidos: ${context.parsed.y}`;
                            } else {
                                return `Horas Perdidas: ${item.horas_perdidas || 0} (${context.parsed.y.toFixed(1)} dias equiv.)`;
                            }
                        }
                    }
                }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderizarChartFrequenciaAtestados(dados) {
    const ctx = document.getElementById('chartFrequenciaAtestados');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartFrequenciaAtestados) chartFrequenciaAtestados.destroy();
    
    chartFrequenciaAtestados = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: dados.map(d => d.frequencia),
            datasets: [{
                label: 'Funcionários',
                data: dados.map(d => d.quantidade),
                backgroundColor: PALETA_EMPRESA.slice(0, 5)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { font: { size: 11 } } }
            }
        }
    });
}

function renderizarChartProdutividade(dados) {
    const ctx = document.getElementById('chartProdutividade');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartProdutividade) chartProdutividade.destroy();
    
    // Agrupa por mês
    const dadosPorMes = {};
    dados.forEach(d => {
        const mesRef = d.mes_referencia || 'sem-mes';
        if (!dadosPorMes[mesRef]) {
            dadosPorMes[mesRef] = [];
        }
        dadosPorMes[mesRef].push(d);
    });
    
    // Calcula totais de Agendados e Faltas por categoria (soma de todos os meses)
    const totaisAgendados = {
        ocupacionais: 0,
        assistenciais: 0,
        acidente_trabalho: 0,
        inss: 0,
        sinistralidade: 0,
        absenteismo: 0,
        pericia_indireta: 0
    };
    
    const totaisFaltas = {
        ocupacionais: 0,
        assistenciais: 0,
        acidente_trabalho: 0,
        inss: 0,
        sinistralidade: 0,
        absenteismo: 0,
        pericia_indireta: 0
    };
    
    Object.values(dadosPorMes).forEach(dadosMes => {
        // Busca os registros de "Agendados" e "Compareceram" para este mês
        const agendados = dadosMes.find(d => d.tipo_consulta === 'Agendados');
        const compareceram = dadosMes.find(d => d.tipo_consulta === 'Compareceram');
        
        if (agendados) {
            totaisAgendados.ocupacionais += (agendados.ocupacionais || 0);
            totaisAgendados.assistenciais += (agendados.assistenciais || 0);
            totaisAgendados.acidente_trabalho += (agendados.acidente_trabalho || 0);
            totaisAgendados.inss += (agendados.inss || 0);
            totaisAgendados.sinistralidade += (agendados.sinistralidade || 0);
            totaisAgendados.absenteismo += (agendados.absenteismo || 0);
            totaisAgendados.pericia_indireta += (agendados.pericia_indireta || 0);
        }
        
        if (agendados && compareceram) {
            // Calcula faltas: Agendados - Compareceram
            totaisFaltas.ocupacionais += Math.max(0, (agendados.ocupacionais || 0) - (compareceram.ocupacionais || 0));
            totaisFaltas.assistenciais += Math.max(0, (agendados.assistenciais || 0) - (compareceram.assistenciais || 0));
            totaisFaltas.acidente_trabalho += Math.max(0, (agendados.acidente_trabalho || 0) - (compareceram.acidente_trabalho || 0));
            totaisFaltas.inss += Math.max(0, (agendados.inss || 0) - (compareceram.inss || 0));
            totaisFaltas.sinistralidade += Math.max(0, (agendados.sinistralidade || 0) - (compareceram.sinistralidade || 0));
            totaisFaltas.absenteismo += Math.max(0, (agendados.absenteismo || 0) - (compareceram.absenteismo || 0));
            totaisFaltas.pericia_indireta += Math.max(0, (agendados.pericia_indireta || 0) - (compareceram.pericia_indireta || 0));
        }
    });
    
    // Calcula compareceram (Agendados - Faltas) para mostrar na barra empilhada
    const totaisCompareceram = {
        ocupacionais: totaisAgendados.ocupacionais - totaisFaltas.ocupacionais,
        assistenciais: totaisAgendados.assistenciais - totaisFaltas.assistenciais,
        acidente_trabalho: totaisAgendados.acidente_trabalho - totaisFaltas.acidente_trabalho,
        inss: totaisAgendados.inss - totaisFaltas.inss,
        sinistralidade: totaisAgendados.sinistralidade - totaisFaltas.sinistralidade,
        absenteismo: totaisAgendados.absenteismo - totaisFaltas.absenteismo,
        pericia_indireta: totaisAgendados.pericia_indireta - totaisFaltas.pericia_indireta
    };
    
    // Determina o período (ano e mês mais recente)
    const meses = Object.keys(dadosPorMes).sort();
    let periodoTexto = '';
    if (meses.length > 0) {
        const mesMaisRecente = meses[meses.length - 1]; // YYYY-MM
        const [ano, mes] = mesMaisRecente.split('-');
        const mesesNomes = {
            '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março', '04': 'Abril',
            '05': 'Maio', '06': 'Junho', '07': 'Julho', '08': 'Agosto',
            '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
        };
        periodoTexto = `Ano ${ano} até ${mesesNomes[mes] || mes}`;
    }
    
    // Cria array de categorias com seus totais para ordenação
    const categorias = [
        { nome: 'Ocupacionais', key: 'ocupacionais' },
        { nome: 'Assistenciais', key: 'assistenciais' },
        { nome: 'Acidente de Trabalho', key: 'acidente_trabalho' },
        { nome: 'INSS', key: 'inss' },
        { nome: 'Sinistralidade', key: 'sinistralidade' },
        { nome: 'Absenteísmo', key: 'absenteismo' },
        { nome: 'Perícia Indireta', key: 'pericia_indireta' }
    ];
    
    // Ordena em ordem decrescente pelo total de agendados
    categorias.sort((a, b) => {
        const totalA = totaisAgendados[a.key] || 0;
        const totalB = totaisAgendados[b.key] || 0;
        return totalB - totalA;
    });
    
    // Prepara os dados ordenados
    const labelsOrdenados = categorias.map(c => c.nome);
    const dataCompareceram = categorias.map(c => Math.max(0, totaisCompareceram[c.key]));
    const dataFaltas = categorias.map(c => totaisFaltas[c.key]);
    
    chartProdutividade = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labelsOrdenados,
            datasets: [
                {
                    label: 'Compareceram',
                    data: dataCompareceram,
                    backgroundColor: '#0056b3',
                    borderRadius: { topLeft: 6, topRight: 6, bottomLeft: 0, bottomRight: 0 }
                },
                {
                    label: 'Faltas',
                    data: dataFaltas,
                    backgroundColor: '#dc3545',
                    borderRadius: { topLeft: 0, topRight: 0, bottomLeft: 6, bottomRight: 6 }
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: periodoTexto || 'Produtividade - Consultas por Categoria',
                    font: {
                        size: 14,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                },
                legend: { 
                    display: true,
                    position: 'top',
                    labels: {
                        font: { size: 12 },
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            const index = context.dataIndex;
                            const categoriaKey = categorias[index].key;
                            const total = totaisAgendados[categoriaKey];
                            const percent = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} consultas (${percent}%)`;
                        },
                        footer: function(tooltipItems) {
                            if (tooltipItems.length > 0) {
                                const index = tooltipItems[0].dataIndex;
                                const categoriaKey = categorias[index].key;
                                const total = totaisAgendados[categoriaKey];
                                const compareceram = totaisCompareceram[categoriaKey];
                                const faltas = totaisFaltas[categoriaKey];
                                const percentCompareceram = total > 0 ? ((compareceram / total) * 100).toFixed(1) : 0;
                                const percentFaltas = total > 0 ? ((faltas / total) * 100).toFixed(1) : 0;
                                return [
                                    `Total Agendados: ${total} consultas`,
                                    `Comparecimento: ${percentCompareceram}%`,
                                    `Faltas: ${percentFaltas}%`
                                ];
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                y: { 
                    beginAtZero: true,
                    stacked: true,
                    ticks: { font: { size: 11 }, stepSize: 1 }
                },
                x: { 
                    stacked: true,
                    ticks: { font: { size: 11 } },
                    grid: { display: false }
                }
            }
        }
    });
}

// ==================== PRODUTIVIDADE MENSAL POR CATEGORIA ====================
function renderizarChartProdutividadeMensalCategoria(dados) {
    const ctx = document.getElementById('chartProdutividadeMensalCategoria');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartProdutividadeMensalCategoria) chartProdutividadeMensalCategoria.destroy();
    
    // Agrupa por mês
    const dadosPorMes = {};
    dados.forEach(d => {
        const mesRef = d.mes_referencia || 'sem-mes';
        if (!dadosPorMes[mesRef]) {
            dadosPorMes[mesRef] = [];
        }
        dadosPorMes[mesRef].push(d);
    });
    
    // Ordena os meses
    const mesesOrdenados = Object.keys(dadosPorMes).sort();
    
    // Formata labels de mês
    const mesesNomes = {
        '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
        '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
        '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
    };
    
    const labels = mesesOrdenados.map(mesRef => {
        const [ano, mes] = mesRef.split('-');
        return `${mesesNomes[mes] || mes}/${ano}`;
    });
    
    // Categorias com cores da empresa: gradiente do azul marinho (#1a237e) ao verde oliva (#556B2F)
    const categorias = [
        { nome: 'Ocupacionais', key: 'ocupacionais', cor: '#1a237e' }, // Azul marinho
        { nome: 'Assistenciais', key: 'assistenciais', cor: '#283593' }, // Azul marinho claro
        { nome: 'Acidente de Trabalho', key: 'acidente_trabalho', cor: '#3949ab' }, // Azul intermediário
        { nome: 'INSS', key: 'inss', cor: '#5c6bc0' }, // Azul mais claro
        { nome: 'Sinistralidade', key: 'sinistralidade', cor: '#6B8E23' }, // Verde oliva claro
        { nome: 'Absenteísmo', key: 'absenteismo', cor: '#556B2F' }, // Verde oliva
        { nome: 'Perícia Indireta', key: 'pericia_indireta', cor: '#4a5d23' } // Verde oliva escuro
    ];
    
    // Prepara datasets para cada categoria
    const datasets = categorias.map(categoria => {
        const data = mesesOrdenados.map(mesRef => {
            const dadosMes = dadosPorMes[mesRef];
            const agendados = dadosMes.find(d => d.tipo_consulta === 'Agendados');
            return agendados ? (agendados[categoria.key] || 0) : 0;
        });
        
        return {
            label: categoria.nome,
            data: data,
            backgroundColor: categoria.cor,
            borderRadius: 4
        };
    });
    
    chartProdutividadeMensalCategoria = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: { size: 11 },
                        usePointStyle: true,
                        padding: 12
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            
                            // Calcula o total do mês
                            const mesIndex = context.dataIndex;
                            const mesRef = mesesOrdenados[mesIndex];
                            const dadosMes = dadosPorMes[mesRef];
                            const agendados = dadosMes.find(d => d.tipo_consulta === 'Agendados');
                            
                            let totalMes = 0;
                            if (agendados) {
                                categorias.forEach(cat => {
                                    totalMes += (agendados[cat.key] || 0);
                                });
                            }
                            
                            const percent = totalMes > 0 ? ((value / totalMes) * 100).toFixed(1) : 0;
                            return `${label}: ${value} consultas (${percent}%)`;
                        },
                        footer: function(tooltipItems) {
                            if (tooltipItems.length > 0) {
                                const mesIndex = tooltipItems[0].dataIndex;
                                const mesRef = mesesOrdenados[mesIndex];
                                const dadosMes = dadosPorMes[mesRef];
                                const agendados = dadosMes.find(d => d.tipo_consulta === 'Agendados');
                                
                                let totalMes = 0;
                                if (agendados) {
                                    categorias.forEach(cat => {
                                        totalMes += (agendados[cat.key] || 0);
                                    });
                                }
                                
                                return `Total do Mês: ${totalMes} consultas`;
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        font: { size: 11 }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        font: { size: 11 },
                        stepSize: 5
                    },
                    title: {
                        display: true,
                        text: 'Quantidade de Consultas',
                        font: { size: 12, weight: 'bold' }
                    }
                }
            }
        }
    });
}

// ==================== EVOLUÇÃO PRODUTIVIDADE ====================
async function carregarEvolucaoProdutividade() {
    try {
        const clientId = getClientId();
        if (!clientId) return;
        
        // Busca dados agregados por mês
        const response = await fetch(`/api/produtividade/evolucao?client_id=${clientId}&agrupar_por=mes`);
        
        if (!response.ok) {
            console.warn('Erro ao carregar evolução de produtividade');
            return;
        }
        
        const data = await response.json();
        const dadosEvolucao = data.data || [];
        
        renderizarChartProdutividadeEvolucao(dadosEvolucao);
        
    } catch (error) {
        console.error('Erro ao carregar evolução de produtividade:', error);
    }
}

function renderizarChartProdutividadeEvolucao(dados) {
    const ctx = document.getElementById('chartProdutividadeEvolucao');
    if (!ctx) return;
    
    if (chartProdutividadeEvolucao) chartProdutividadeEvolucao.destroy();
    
    if (!dados || dados.length === 0) {
        // Mostra mensagem de sem dados
        ctx.parentElement.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #6c757d;">
                <div style="text-align: center;">
                    <i class="fas fa-chart-line" style="font-size: 48px; margin-bottom: 16px; opacity: 0.3;"></i>
                    <p>Nenhum dado de produtividade cadastrado</p>
                    <p style="font-size: 12px; margin-top: 8px;">Cadastre dados em "Produtividade" para ver a evolução</p>
                </div>
            </div>
        `;
        return;
    }
    
    // Formata labels de mês (YYYY-MM -> MMM/YYYY)
    const meses = {
        '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
        '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
        '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
    };
    
    const labels = dados.map(d => {
        if (d.periodo && d.periodo.includes('-')) {
            const [ano, mes] = d.periodo.split('-');
            return `${meses[mes] || mes}/${ano}`;
        }
        return d.periodo;
    });
    
    chartProdutividadeEvolucao = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Total de Consultas',
                    data: dados.map(d => d.total || 0),
                    borderColor: CORES_EMPRESA.primary,
                    backgroundColor: 'rgba(26, 35, 126, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Ocupacionais',
                    data: dados.map(d => d.ocupacionais || 0),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Assistenciais',
                    data: dados.map(d => d.assistenciais || 0),
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Acidente de Trabalho',
                    data: dados.map(d => d.acidente_trabalho || 0),
                    borderColor: '#ff9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    tension: 0.4,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'INSS',
                    data: dados.map(d => d.inss || 0),
                    borderColor: '#9c27b0',
                    backgroundColor: 'rgba(156, 39, 176, 0.1)',
                    tension: 0.4,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Sinistralidade',
                    data: dados.map(d => d.sinistralidade || 0),
                    borderColor: '#00bcd4',
                    backgroundColor: 'rgba(0, 188, 212, 0.1)',
                    tension: 0.4,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Absenteísmo',
                    data: dados.map(d => d.absenteismo || 0),
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.4,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Perícia Indireta',
                    data: dados.map(d => d.pericia_indireta || 0),
                    borderColor: '#795548',
                    backgroundColor: 'rgba(121, 85, 72, 0.1)',
                    tension: 0.4,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 3,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: { size: 11 },
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} consultas`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: { size: 11 },
                        stepSize: 5,
                        maxTicksLimit: 10
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    title: {
                        display: true,
                        text: 'Quantidade de Consultas',
                        font: { size: 12, weight: 'bold' }
                    }
                },
                x: {
                    ticks: {
                        font: { size: 11 }
                    },
                    title: {
                        display: true,
                        text: 'Período',
                        font: { size: 12, weight: 'bold' }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

function renderizarChartSetorGenero(dados) {
    const ctx = document.getElementById('chartSetorGenero');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (chartSetorGenero) chartSetorGenero.destroy();
    
    // Calcula total geral para calcular percentuais
    const totalGeral = dados.reduce((sum, d) => sum + (d.dias_perdidos || 0), 0);
    
    // Agrupa por setor e calcula total por setor
    const setoresMap = {};
    dados.forEach(d => {
        if (!setoresMap[d.setor]) {
            setoresMap[d.setor] = {
                setor: d.setor,
                total: 0,
                M: 0,
                F: 0
            };
        }
        const dias = d.dias_perdidos || 0;
        setoresMap[d.setor].total += dias;
        if (d.genero === 'M') {
            setoresMap[d.setor].M += dias;
        } else if (d.genero === 'F') {
            setoresMap[d.setor].F += dias;
        }
    });
    
    // Converte para array e ordena por total (incidência)
    const setoresOrdenados = Object.values(setoresMap)
        .sort((a, b) => b.total - a.total)
        .slice(0, 10); // TOP 10
    
    const setores = setoresOrdenados.map(s => s.setor);
    const generos = ['M', 'F'];
    // Azul Marinho para Masculino, Verde Oliva para Feminino
    const cores = { 'M': CORES_EMPRESA.primary, 'F': CORES_EMPRESA.secondary };
    
    // Prepara dados com percentuais
    const datasets = generos.map(genero => {
        const label = genero === 'M' ? 'Masculino' : 'Feminino';
        const data = setores.map(setor => {
            const item = setoresOrdenados.find(s => s.setor === setor);
            return item ? (item[genero] || 0) : 0;
        });
        
        // Calcula percentuais para tooltip
        const percentuais = data.map(valor => {
            return totalGeral > 0 ? ((valor / totalGeral) * 100).toFixed(2) : '0.00';
        });
        
        return {
            label: label,
            data: data,
            backgroundColor: cores[genero],
            borderRadius: 6,
            percentuais: percentuais
        };
    });
    
    chartSetorGenero = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: setores.map(s => truncate(s, 25)),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: 'top', 
                    labels: { 
                        font: { size: 12 },
                        padding: 15,
                        boxWidth: 20,
                        boxHeight: 12
                    } 
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 13, weight: 'bold' },
                    bodyFont: { size: 12 },
                    callbacks: {
                        label: function(context) {
                            const datasetIndex = context.datasetIndex;
                            const dataIndex = context.dataIndex;
                            const valor = context.parsed.y;
                            const percentual = context.dataset.percentuais[dataIndex];
                            const totalSetor = setoresOrdenados[dataIndex].total;
                            const percentualSetor = totalGeral > 0 ? ((totalSetor / totalGeral) * 100).toFixed(2) : '0.00';
                            
                            return [
                                `${context.dataset.label}: ${valor} dias`,
                                `Percentual do Total: ${percentual}%`,
                                `Total do Setor: ${totalSetor} dias (${percentualSetor}%)`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: { 
                    beginAtZero: true,
                    ticks: { 
                        font: { size: 11 },
                        stepSize: 1,
                        precision: 0
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        lineWidth: 1
                    },
                    title: {
                        display: true,
                        text: 'Dias Perdidos',
                        font: { size: 12, weight: 'bold' }
                    }
                },
                x: {
                    ticks: { 
                        font: { size: 11 }
                    },
                    grid: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Setor',
                        font: { size: 12, weight: 'bold' }
                    }
                }
            }
        }
    });
}

// ==================== FILTROS ====================
async function aplicarFiltros() {
    const clientId = getClientId();
    if (!clientId) {
        alert('Selecione um cliente na aba "Clientes" para aplicar filtros.');
        return;
    }

    const mesInicio = document.getElementById('mesInicio')?.value || '';
    const mesFim = document.getElementById('mesFim')?.value || '';
    
    // Pega múltiplos funcionários selecionados
    const selectFuncionario = document.getElementById('filtroFuncionario');
    const funcionarios = Array.from(selectFuncionario?.selectedOptions || [])
        .map(option => option.value)
        .filter(v => v);
    
    // Pega múltiplos setores selecionados
    const selectSetor = document.getElementById('filtroSetor');
    const setores = Array.from(selectSetor?.selectedOptions || [])
        .map(option => option.value)
        .filter(v => v);
    
    let url = `/api/dashboard?client_id=${clientId}`;
    if (mesInicio) url += `&mes_inicio=${encodeURIComponent(mesInicio)}`;
    if (mesFim) url += `&mes_fim=${encodeURIComponent(mesFim)}`;
    
    // Adiciona múltiplos funcionários
    funcionarios.forEach(func => {
        url += `&funcionario=${encodeURIComponent(func)}`;
    });
    
    // Adiciona múltiplos setores
    setores.forEach(setor => {
        url += `&setor=${encodeURIComponent(setor)}`;
    });
    
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erro ${response.status}`);
        
        const data = await response.json();
        
        renderizarCards(data.metricas || {});
        renderizarInsights(data.insights || []);
        renderizarChartCids(data.top_cids || []);
        renderizarChartSetores(data.top_setores || []);
        renderizarChartEvolucao(data.evolucao_mensal || []);
        renderizarChartGenero(data.distribuicao_genero || []);
        renderizarChartMediaCid(data.top_cids || []);
        renderizarChartFuncionariosDias(data.top_funcionarios || []);
        renderizarChartEscalas(data.top_escalas || []);
        renderizarChartMotivos(data.top_motivos || []);
        renderizarChartCentroCusto(data.dias_centro_custo || []);
        renderizarChartDistribuicaoDias(data.distribuicao_dias || []);
        renderizarChartMediaCidDias(data.media_cid || []);
        renderizarChartEvolucaoSetor(data.evolucao_setor || {});
        renderizarChartComparativoDiasHoras(data.comparativo_dias_horas || []);
        renderizarChartFrequenciaAtestados(data.frequencia_atestados || []);
        renderizarChartSetorGenero(data.dias_setor_genero || []);
        renderizarChartProdutividade(data.produtividade || []);
        
        // Armazena alertas para o menu
        window.alertasData = data.alertas || [];
        if (typeof carregarAlertasMenu === 'function') {
            carregarAlertasMenu();
        }
        
    } catch (error) {
        console.error('Erro ao aplicar filtros:', error);
        alert('Erro ao aplicar filtros: ' + error.message);
    }
}

function recarregarDados() {
    limparFiltros();
    carregarDashboard();
}

function limparFiltros() {
    const mesInicio = document.getElementById('mesInicio');
    const mesFim = document.getElementById('mesFim');
    
    if (mesInicio) mesInicio.value = '';
    if (mesFim) mesFim.value = '';
    
    // Desmarca todos os checkboxes de funcionários
    const containerFuncionarios = document.getElementById('checkboxesFuncionarios');
    if (containerFuncionarios) {
        const checkboxes = containerFuncionarios.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
    }
    
    // Desmarca todos os checkboxes de setores
    const containerSetores = document.getElementById('checkboxesSetores');
    if (containerSetores) {
        const checkboxes = containerSetores.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
    }
}

async function carregarFiltros() {
    try {
        const clientId = getClientId();
        if (!clientId) {
            const containerFuncionarios = document.getElementById('checkboxesFuncionarios');
            const containerSetores = document.getElementById('checkboxesSetores');
            if (containerFuncionarios) containerFuncionarios.innerHTML = '<div style="text-align: center; padding: 20px; color: #6c757d;">Selecione um cliente para ver funcionários.</div>';
            if (containerSetores) containerSetores.innerHTML = '<div style="text-align: center; padding: 20px; color: #6c757d;">Selecione um cliente para ver setores.</div>';
            return;
        }
        const response = await fetch(`/api/filtros?client_id=${clientId}`);
        if (!response.ok) throw new Error('Erro ao carregar filtros');
        
        const data = await response.json();
        
        // Preenche checkboxes de funcionários
        const containerFuncionarios = document.getElementById('checkboxesFuncionarios');
        if (containerFuncionarios && data.funcionarios) {
            containerFuncionarios.innerHTML = '';
            data.funcionarios.forEach(func => {
                const label = document.createElement('label');
                label.style.cssText = 'display: flex; align-items: center; padding: 8px; cursor: pointer; border-radius: 4px; transition: background 0.2s;';
                label.onmouseover = () => label.style.background = '#f0f0f0';
                label.onmouseout = () => label.style.background = 'transparent';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = func;
                checkbox.id = `func_${func.replace(/\s+/g, '_')}`;
                checkbox.style.cssText = 'margin-right: 8px; cursor: pointer; width: 18px; height: 18px;';
                checkbox.addEventListener('change', () => atualizarTextoSelecionados('funcionarios'));
                
                const span = document.createElement('span');
                span.textContent = func;
                span.style.cssText = 'flex: 1; font-size: 14px; color: #333;';
                
                label.appendChild(checkbox);
                label.appendChild(span);
                containerFuncionarios.appendChild(label);
            });
        }
        
        // Preenche checkboxes de setores
        const containerSetores = document.getElementById('checkboxesSetores');
        if (containerSetores && data.setores) {
            containerSetores.innerHTML = '';
            data.setores.forEach(setor => {
                const label = document.createElement('label');
                label.style.cssText = 'display: flex; align-items: center; padding: 8px; cursor: pointer; border-radius: 4px; transition: background 0.2s;';
                label.onmouseover = () => label.style.background = '#f0f0f0';
                label.onmouseout = () => label.style.background = 'transparent';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = setor;
                checkbox.id = `setor_${setor.replace(/\s+/g, '_')}`;
                checkbox.style.cssText = 'margin-right: 8px; cursor: pointer; width: 18px; height: 18px;';
                checkbox.addEventListener('change', () => atualizarTextoSelecionados('setores'));
                
                const span = document.createElement('span');
                span.textContent = setor;
                span.style.cssText = 'flex: 1; font-size: 14px; color: #333;';
                
                label.appendChild(checkbox);
                label.appendChild(span);
                containerSetores.appendChild(label);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar filtros:', error);
        const containerFuncionarios = document.getElementById('checkboxesFuncionarios');
        const containerSetores = document.getElementById('checkboxesSetores');
        if (containerFuncionarios) containerFuncionarios.innerHTML = '<div style="text-align: center; padding: 20px; color: #dc3545;">Erro ao carregar funcionários</div>';
        if (containerSetores) containerSetores.innerHTML = '<div style="text-align: center; padding: 20px; color: #dc3545;">Erro ao carregar setores</div>';
    }
}

function toggleDropdown(tipo) {
    const dropdownId = tipo === 'funcionarios' ? 'dropdownFuncionarios' : 'dropdownSetores';
    const iconId = tipo === 'funcionarios' ? 'funcionariosIcon' : 'setoresIcon';
    const dropdown = document.getElementById(dropdownId);
    const icon = document.getElementById(iconId);
    
    // Fecha outros dropdowns
    document.querySelectorAll('.multiselect-dropdown-content').forEach(dd => {
        if (dd.id !== dropdownId) {
            dd.style.display = 'none';
        }
    });
    document.querySelectorAll('.multiselect-dropdown i').forEach(ic => {
        if (ic.id !== iconId) {
            ic.style.transform = 'rotate(0deg)';
        }
    });
    
    // Toggle do dropdown atual
    if (dropdown.style.display === 'none' || !dropdown.style.display) {
        dropdown.style.display = 'block';
        if (icon) icon.style.transform = 'rotate(180deg)';
    } else {
        dropdown.style.display = 'none';
        if (icon) icon.style.transform = 'rotate(0deg)';
    }
    
    // Atualiza texto após seleção
    setTimeout(() => atualizarTextoSelecionados(tipo), 100);
}

function atualizarTextoSelecionados(tipo) {
    const containerId = tipo === 'funcionarios' ? 'checkboxesFuncionarios' : 'checkboxesSetores';
    const textId = tipo === 'funcionarios' ? 'funcionariosText' : 'setoresText';
    const container = document.getElementById(containerId);
    const textEl = document.getElementById(textId);
    
    if (container && textEl) {
        const checkboxes = container.querySelectorAll('input[type="checkbox"]:checked');
        const count = checkboxes.length;
        
        if (count === 0) {
            textEl.textContent = 'Selecione...';
            textEl.style.color = '#6c757d';
        } else {
            textEl.textContent = `${count} ${tipo === 'funcionarios' ? 'func.' : 'setor(es)'} selecionado(s)`;
            textEl.style.color = '#1a237e';
        }
    }
}

function selecionarTodos(tipo) {
    const containerId = tipo === 'funcionarios' ? 'checkboxesFuncionarios' : 'checkboxesSetores';
    const container = document.getElementById(containerId);
    if (container) {
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            cb.checked = true;
            cb.dispatchEvent(new Event('change'));
        });
    }
    atualizarTextoSelecionados(tipo);
}

function desselecionarTodos(tipo) {
    const containerId = tipo === 'funcionarios' ? 'checkboxesFuncionarios' : 'checkboxesSetores';
    const container = document.getElementById(containerId);
    if (container) {
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            cb.checked = false;
            cb.dispatchEvent(new Event('change'));
        });
    }
    atualizarTextoSelecionados(tipo);
}

// ==================== UTILITÁRIOS ====================
function truncate(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
}

