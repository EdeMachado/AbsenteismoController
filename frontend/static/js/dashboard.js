/**
 * Dashboard JavaScript - AbsenteismoController v2.0
 */

let chartCids, chartSetores, chartEvolucao, chartGenero, chartTipoAtestado, chartMediaCid;

// Inicializa o dashboard
document.addEventListener('DOMContentLoaded', () => {
    carregarDashboard();
    carregarFiltros();
});

async function carregarDashboard() {
    try {
        const response = await fetch('/api/dashboard?client_id=1');
        const data = await response.json();
        
        renderizarMetricas(data.metricas);
        renderizarInsights(data.insights);
        renderizarChartCids(data.top_cids);
        renderizarChartSetores(data.top_setores);
        renderizarChartEvolucao(data.evolucao_mensal);
        renderizarChartGenero(data.distribuicao_genero);
        renderizarChartTipoAtestado(data.metricas);
        renderizarChartMediaCid(data.top_cids);
        
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        alert('Erro ao carregar dados. Verifique se existem uploads.');
    }
}

function renderizarMetricas(metricas) {
    document.getElementById('atestadosDias').textContent = metricas.total_atestados_dias.toLocaleString('pt-BR');
    document.getElementById('atestadosHoras').textContent = metricas.total_atestados_horas.toLocaleString('pt-BR');
    document.getElementById('diasPerdidos').textContent = Math.round(metricas.total_dias_perdidos).toLocaleString('pt-BR');
    document.getElementById('horasPerdidas').textContent = Math.round(metricas.total_horas_perdidas).toLocaleString('pt-BR');
}

function renderizarInsights(insights) {
    const container = document.getElementById('insightsContainer');
    const section = document.getElementById('insightsSection');
    
    if (!insights || insights.length === 0) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    
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

function renderizarChartCids(dados) {
    const ctx = document.getElementById('chartCids');
    
    // Destroy previous chart
    if (chartCids) chartCids.destroy();
    
    // Verifica se há dados
    if (!dados || dados.length === 0) {
        ctx.parentElement.innerHTML = '<div class="no-data">Nenhum dado de CID disponível</div>';
        return;
    }
    
    chartCids = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dados.map(d => truncate(d.descricao || d.cid, 28)),
            datasets: [{
                label: 'Atestados',
                data: dados.map(d => d.quantidade),
                backgroundColor: '#1976D2',
                borderRadius: 6,
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
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            return `${dados[index].cid} - ${dados[index].descricao || 'Não especificado'}`;
                        },
                        label: function(context) {
                            return `Atestados: ${context.parsed.x}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        font: { size: 10 }
                    }
                },
                y: {
                    ticks: {
                        font: { size: 10 }
                    }
                }
            }
        }
    });
}

function renderizarChartSetores(dados) {
    const ctx = document.getElementById('chartSetores');
    
    if (chartSetores) chartSetores.destroy();
    
    // Verifica se há dados
    if (!dados || dados.length === 0) {
        ctx.parentElement.innerHTML = '<div class="no-data">Nenhum dado de setor disponível</div>';
        return;
    }
    
    chartSetores = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dados.map(d => truncate(d.setor, 15)),
            datasets: [{
                label: 'Atestados',
                data: dados.map(d => d.quantidade),
                backgroundColor: '#FF9800',
                borderRadius: 6,
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
                    ticks: {
                        precision: 0,
                        font: { size: 10 }
                    }
                },
                x: {
                    ticks: {
                        font: { size: 10 }
                    }
                }
            }
        }
    });
}

function renderizarChartEvolucao(dados) {
    const ctx = document.getElementById('chartEvolucao');
    
    if (chartEvolucao) chartEvolucao.destroy();
    
    chartEvolucao = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dados.map(d => formatarMes(d.mes)),
            datasets: [
                {
                    label: 'Atestados',
                    data: dados.map(d => d.quantidade),
                    borderColor: '#1976D2',
                    backgroundColor: 'rgba(25, 118, 210, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    borderWidth: 2
                },
                {
                    label: 'Dias Perdidos',
                    data: dados.map(d => d.dias_perdidos),
                    borderColor: '#FF9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    borderWidth: 2
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
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        font: { size: 10 }
                    }
                },
                x: {
                    ticks: {
                        font: { size: 10 }
                    }
                }
            }
        }
    });
}

function renderizarChartGenero(dados) {
    const ctx = document.getElementById('chartGenero');
    
    if (chartGenero) chartGenero.destroy();
    
    const cores = {
        'M': '#2196F3',
        'F': '#E91E63',
        'O': '#9C27B0'
    };
    
    const labels = {
        'M': 'Masculino',
        'F': 'Feminino',
        'O': 'Outro'
    };
    
    chartGenero = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: dados.map(d => labels[d.genero] || d.genero),
            datasets: [{
                data: dados.map(d => d.quantidade),
                backgroundColor: dados.map(d => cores[d.genero] || '#757575'),
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
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function renderizarChartTipoAtestado(metricas) {
    const ctx = document.getElementById('chartTipoAtestado');
    
    if (chartTipoAtestado) chartTipoAtestado.destroy();
    
    chartTipoAtestado = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Dias', 'Horas'],
            datasets: [{
                data: [metricas.total_atestados_dias, metricas.total_atestados_horas],
                backgroundColor: ['#4CAF50', '#2196F3'],
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
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function renderizarChartMediaCid(dados) {
    const ctx = document.getElementById('chartMediaCid');
    
    if (chartMediaCid) chartMediaCid.destroy();
    
    // Pega TOP 5 CIDs com mais dias perdidos
    const top5 = dados.slice(0, 5);
    
    chartMediaCid = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top5.map(d => truncate(d.descricao || d.cid, 18)),
            datasets: [{
                label: 'Dias',
                data: top5.map(d => d.dias_perdidos),
                backgroundColor: '#FF9800',
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            return `${top5[index].cid} - ${top5[index].descricao}`;
                        },
                        label: function(context) {
                            return `Dias Perdidos: ${context.parsed.y.toFixed(1)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        font: { size: 10 }
                    }
                },
                x: {
                    ticks: {
                        font: { size: 9 },
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

async function aplicarFiltros() {
    const mesInicio = document.getElementById('mesInicio').value;
    const mesFim = document.getElementById('mesFim').value;
    
    let url = '/api/dashboard?client_id=1';
    if (mesInicio) url += `&mes_inicio=${mesInicio}`;
    if (mesFim) url += `&mes_fim=${mesFim}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        renderizarMetricas(data.metricas);
        renderizarInsights(data.insights);
        renderizarChartCids(data.top_cids);
        renderizarChartSetores(data.top_setores);
        renderizarChartEvolucao(data.evolucao_mensal);
        renderizarChartGenero(data.distribuicao_genero);
        renderizarChartTipoAtestado(data.metricas);
        renderizarChartMediaCid(data.top_cids);
        
    } catch (error) {
        console.error('Erro ao aplicar filtros:', error);
        alert('Erro ao aplicar filtros');
    }
}

function recarregarDados() {
    document.getElementById('mesInicio').value = '';
    document.getElementById('mesFim').value = '';
    document.getElementById('filtroFuncionario').value = '';
    document.getElementById('filtroSetor').value = '';
    carregarDashboard();
}

async function carregarFiltros() {
    try {
        const response = await fetch('/api/analises/funcionarios?client_id=1');
        const funcionarios = await response.json();
        
        // Extrair listas únicas
        const nomes = [...new Set(funcionarios.map(f => f.nome).filter(n => n))].sort();
        const setores = [...new Set(funcionarios.map(f => f.setor).filter(s => s))].sort();
        
        // Popular dropdowns
        const selectFunc = document.getElementById('filtroFuncionario');
        selectFunc.innerHTML = '<option value="">Todos</option>' +
            nomes.map(n => `<option value="${n}">${n}</option>`).join('');
        
        const selectSetor = document.getElementById('filtroSetor');
        selectSetor.innerHTML = '<option value="">Todos</option>' +
            setores.map(s => `<option value="${s}">${s}</option>`).join('');
        
    } catch (error) {
        console.log('Aguardando upload de dados...');
    }
}

// Utilities
function formatarMes(mes) {
    const [ano, mesNum] = mes.split('-');
    const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    return `${meses[parseInt(mesNum) - 1]}/${ano}`;
}

function truncate(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
}

