// ==================== VARIÁVEIS GLOBAIS ====================
let slides = [];
let slideAtual = 0;
let charts = {};

// Paleta de Cores da Empresa
const CORES_EMPRESA = {
    primary: '#1a237e',
    primaryDark: '#0d47a1',
    primaryLight: '#3949ab',
    secondary: '#556B2F',
    secondaryDark: '#4a5d23',
    secondaryLight: '#6B8E23',
};

const PALETA_EMPRESA = [
    '#1a237e', '#556B2F', '#3949ab', '#6B8E23', '#0d47a1', '#808000'
];

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    // Aguarda um pouco para garantir que auth.js carregou
    setTimeout(() => {
        console.log('Inicializando apresentação...');
        carregarApresentacao();
    }, 500);
    
    // Navegação por teclado
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') slideAnterior();
        if (e.key === 'ArrowRight') proximoSlide();
        if (e.key === 'Escape') sairApresentacao();
    });
});

// ==================== CARREGAR APRESENTAÇÃO ====================
async function carregarApresentacao(forceClientId = null) {
    try {
        // Sempre obtém o client_id atual do localStorage (sem valor padrão)
        let clientId = forceClientId;
        
        if (!clientId) {
            if (typeof window.getCurrentClientId === 'function') {
                clientId = window.getCurrentClientId(null);
            } else {
                const stored = localStorage.getItem('cliente_selecionado');
                clientId = stored ? Number(stored) : null;
            }
        }
        
        // Converte para número se for string
        if (typeof clientId === 'string') {
            clientId = Number(clientId);
        }
        
        // Valida se é um número válido
        if (!clientId || !Number.isFinite(clientId) || clientId <= 0 || clientId === 'null' || clientId === 'undefined') {
            mostrarErro('Selecione um cliente para visualizar a apresentação');
            return;
        }
        
        console.log('Carregando apresentação para cliente ID:', clientId);
        
        // Adiciona timestamp para evitar cache
        const timestamp = new Date().getTime();
        const response = await fetch(`/api/apresentacao?client_id=${clientId}&_t=${timestamp}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Erro ao carregar apresentação: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        slides = data.slides || [];
        
        console.log('Slides carregados:', slides.length, 'para cliente:', clientId);
        
        document.getElementById('totalSlides').textContent = slides.length;
        
        if (slides.length > 0) {
            slideAtual = 0;
            renderizarSlide(slides[0]);
            atualizarBotoes();
        } else {
            mostrarErro('Nenhum dado disponível para apresentação');
        }
    } catch (error) {
        console.error('Erro ao carregar apresentação:', error);
        mostrarErro('Erro ao carregar apresentação: ' + error.message);
    }
}

// Recarrega quando o cliente muda
if (typeof window !== 'undefined') {
    // Observa mudanças no localStorage
    window.addEventListener('storage', (e) => {
        if (e.key === 'cliente_selecionado') {
            console.log('Cliente mudou no storage, recarregando apresentação...');
            setTimeout(() => {
                carregarApresentacao();
            }, 300);
        }
    });
    
    // Observa mudanças diretas no localStorage (mesma aba)
    const originalSetItem = localStorage.setItem;
    localStorage.setItem = function(key, value) {
        originalSetItem.apply(this, arguments);
        if (key === 'cliente_selecionado') {
            console.log('Cliente mudou no localStorage, recarregando apresentação...');
            // Recarrega a apresentação quando o cliente muda
            setTimeout(() => {
                const newClientId = Number(value);
                if (newClientId && Number.isFinite(newClientId) && newClientId > 0) {
                    carregarApresentacao(newClientId);
                }
            }, 300);
        }
    };
}

// ==================== RENDERIZAR SLIDE ====================
function renderizarSlide(slide) {
    const container = document.getElementById('slideContent');
    // Não mostra número para capa (id 0) e slides de ações (id >= 14)
    if (slide.id === 0 || slide.id >= 14) {
        document.getElementById('slideAtual').textContent = '-';
    } else {
        document.getElementById('slideAtual').textContent = slide.id;
    }
    
    // Limpa gráficos anteriores
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
    charts = {};
    
    let html = '';
    
    // Renderiza conteúdo baseado no tipo
    if (slide.tipo === 'capa') {
        // Capa não tem header
        html += renderizarCapa();
    } else {
        // Outros slides têm header
        html += `
            <div class="slide-header">
                <h2>${slide.titulo}</h2>
                <p>${slide.subtitulo}</p>
            </div>
        `;
        
        if (slide.tipo === 'kpis') {
            html += `<div class="slide-body">`;
            html += renderizarKPIs(slide.dados);
            // Análise IA para KPIs
            html += `
                <div class="analise-container">
                    <h3>
                        <i class="fas fa-lightbulb"></i>
                        Análise e Insights
                    </h3>
                    <div class="analise-texto">${formatarAnalise(slide.analise)}</div>
                </div>
            `;
            html += `</div>`;
        } else if (slide.tipo === 'produtividade') {
            html += `<div class="slide-body">`;
            html += renderizarProdutividade(slide);
            html += `</div>`;
        } else if (slide.tipo === 'acoes_intro' || slide.tipo === 'acoes_saude_fisica' || slide.tipo === 'acoes_saude_emocional' || slide.tipo === 'acoes_saude_social') {
            // Slides de ações ocupam toda a altura (sem grid de análise)
            html += `<div style="flex: 1; overflow: hidden; position: relative;">`;
            // Botões de edição (apenas para slides de saúde, não para introdução)
            if (slide.tipo !== 'acoes_intro') {
                html += `
                    <div style="position: absolute; top: 10px; right: 10px; z-index: 100; display: flex; gap: 8px;">
                        <button id="btnEditarAcoes" onclick="toggleEdicaoAcoes('${slide.tipo}')" style="padding: 8px 16px; background: #556B2F; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 6px;">
                            <i class="fas fa-edit"></i> Editar
                        </button>
                        <button id="btnSalvarAcoes" onclick="salvarAcoes('${slide.tipo}')" style="padding: 8px 16px; background: #1a237e; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; display: none; align-items: center; gap: 6px;">
                            <i class="fas fa-save"></i> Salvar
                        </button>
                    </div>
                `;
            }
            if (slide.tipo === 'acoes_intro') {
                html += renderizarAcoesIntro(slide.tipo);
            } else if (slide.tipo === 'acoes_saude_fisica') {
                html += renderizarAcoesSaudeFisica(slide.tipo);
            } else if (slide.tipo === 'acoes_saude_emocional') {
                html += renderizarAcoesSaudeEmocional(slide.tipo);
            } else if (slide.tipo === 'acoes_saude_social') {
                html += renderizarAcoesSaudeSocial(slide.tipo);
            }
            // Footer com risco verde/azul e logo CONVER
            html += renderizarFooterAcoes();
            html += `</div>`;
        } else {
            html += `<div class="slide-body">`;
            html += `
                <div class="chart-container-wrapper">
                    <div class="chart-container">
                        <canvas id="chartSlide"></canvas>
                    </div>
                </div>
            `;
            // Análise IA para gráficos
            html += `
                <div class="analise-container">
                    <h3>
                        <i class="fas fa-lightbulb"></i>
                        Análise e Insights
                    </h3>
                    <div class="analise-texto">${formatarAnalise(slide.analise)}</div>
                </div>
            `;
            html += `</div>`;
        }
    }
    
    container.innerHTML = html;
    
    // Renderiza gráfico se necessário
    if (slide.tipo !== 'kpis' && slide.tipo !== 'capa' && slide.tipo !== 'acoes_intro' && slide.tipo !== 'acoes_saude_fisica' && slide.tipo !== 'acoes_saude_emocional' && slide.tipo !== 'acoes_saude_social') {
        setTimeout(() => {
            renderizarGrafico(slide);
        }, 100);
    }
}

// ==================== RENDERIZAR CAPA ====================
function renderizarCapa() {
    return `
        <div style="display: flex; flex-direction: column; height: 100%; width: 100%; background: white; position: relative;">
            <!-- Linha decorativa no topo (verde à esquerda, azul à direita) -->
            <div style="height: 4px; background: linear-gradient(to right, #6B8E23 0%, #6B8E23 50%, #1a237e 50%, #1a237e 100%);"></div>
            
            <!-- Conteúdo principal -->
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 40px; position: relative;">
                <!-- Logo CONVER -->
                <div style="margin-bottom: 60px; display: flex; align-items: center; gap: 0;">
                    <span style="font-size: 72px; font-weight: 700; color: #1a237e; letter-spacing: 2px;">C</span>
                    <div style="width: 72px; height: 72px; position: relative; display: inline-flex; align-items: center; justify-content: center; margin: 0 4px;">
                        <svg width="72" height="72" viewBox="0 0 72 72">
                            <circle cx="36" cy="36" r="32" fill="none" stroke="#6B8E23" stroke-width="4"/>
                            <path d="M 36 8 A 28 28 0 1 1 32 64" fill="none" stroke="#1a237e" stroke-width="3.5" stroke-linecap="round"/>
                            <circle cx="36" cy="12" r="4" fill="#6B8E23"/>
                        </svg>
                    </div>
                    <span style="font-size: 72px; font-weight: 700; color: #1a237e; letter-spacing: 2px;">NVER</span>
                </div>
                
                <!-- Título principal -->
                <div style="text-align: center; margin-bottom: 40px;">
                    <h1 style="font-size: 36px; font-weight: 700; color: #1a237e; margin: 0 0 20px 0; letter-spacing: 1px; line-height: 1.4;">
                        SAÚDE CORPORATIVA - MEDICINA DO TRABALHO
                    </h1>
                    <h2 style="font-size: 32px; font-weight: 600; color: #1a237e; margin: 0; letter-spacing: 0.5px;">
                        INDICADORES DE SAÚDE
                    </h2>
                </div>
                
                <!-- Data no canto inferior direito -->
                <div style="position: absolute; bottom: 40px; right: 60px; text-align: right;">
                    <div style="font-size: 24px; font-weight: 600; color: #1a237e; margin-bottom: 8px; letter-spacing: 0.5px;">
                        OUTUBRO, 2025
                    </div>
                    <div style="font-size: 20px; font-weight: 500; color: #1a237e; letter-spacing: 0.5px;">
                        10/11/2025
                    </div>
                </div>
            </div>
            
            <!-- Linha decorativa na parte inferior (azul à esquerda, verde à direita) -->
            <div style="height: 4px; background: linear-gradient(to right, #1a237e 0%, #1a237e 50%, #6B8E23 50%, #6B8E23 100%);"></div>
        </div>
    `;
}

function renderizarKPIs(dados) {
    // Total de Atestados = número de registros (total_atestados)
    // Dias Perdidos = soma dos dias_atestados
    // Horas Perdidas = soma das horas_perdi
    const totalAtestados = Math.round(dados.total_atestados || dados.total_registros || 0);
    const totalDias = Math.round(dados.total_dias_perdidos || 0);
    const totalHoras = Math.round(dados.total_horas_perdidas || 0);
    
    return `
        <div class="kpis-grid">
            <div class="kpi-card">
                <h3>Total de Atestados</h3>
                <div class="valor">${totalAtestados}</div>
                <div class="label">Atestados</div>
            </div>
            <div class="kpi-card">
                <h3>Dias Perdidos</h3>
                <div class="valor">${totalDias}</div>
                <div class="label">Dias</div>
            </div>
            <div class="kpi-card">
                <h3>Horas Perdidas</h3>
                <div class="valor">${totalHoras}</div>
                <div class="label">Horas</div>
            </div>
        </div>
    `;
}

function renderizarGrafico(slide) {
    const ctx = document.getElementById('chartSlide');
    if (!ctx) return;
    
    const tipo = slide.tipo;
    const dados = slide.dados;
    
    if (!dados || dados.length === 0) {
        return;
    }
    
    let config = {};
    
    switch(tipo) {
        case 'funcionarios_dias':
            // TOP 10 funcionários ordenados por dias perdidos
            const top10Func = dados.slice(0, 10).sort((a, b) => (b.dias_perdidos || 0) - (a.dias_perdidos || 0));
            config = {
                type: 'bar',
                data: {
                    labels: top10Func.map(d => truncate(d.nome || d.nomecompleto || 'N/A', 25)),
                    datasets: [{
                        label: 'Dias Perdidos',
                        data: top10Func.map(d => d.dias_perdidos || 0),
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
                                    const func = top10Func[index];
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
            };
            break;
            
        case 'top_cids':
            config = {
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
            };
            break;
            
        case 'evolucao_mensal':
            config = {
                type: 'line',
                data: {
                    labels: dados.map(d => d.mes || 'N/A'),
                    datasets: [
                        {
                            label: 'Dias Perdidos',
                            data: dados.map(d => d.dias_perdidos || 0),
                            borderColor: CORES_EMPRESA.primary,
                            backgroundColor: CORES_EMPRESA.primaryLight + '40',
                            fill: true,
                            tension: 0.4,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Quantidade de Atestados',
                            data: dados.map(d => d.quantidade || 0),
                            borderColor: CORES_EMPRESA.secondary,
                            backgroundColor: CORES_EMPRESA.secondaryLight + '40',
                            fill: true,
                            tension: 0.4,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
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
                                    const item = dados[index];
                                    if (context.datasetIndex === 0) {
                                        return `Dias Perdidos: ${item.dias_perdidos || 0}`;
                                    } else {
                                        return `Atestados: ${item.quantidade || 0}`;
                                    }
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Dias Perdidos',
                                color: CORES_EMPRESA.primary
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            beginAtZero: true,
                            grid: { drawOnChartArea: false },
                            title: {
                                display: true,
                                text: 'Quantidade de Atestados',
                                color: CORES_EMPRESA.secondary
                            }
                        }
                    }
                }
            };
            break;
            
        case 'top_setores':
            const top5Setores = dados.slice(0, 5);
            config = {
                type: 'line',
                data: {
                    labels: top5Setores.map(d => truncate(d.setor, 20)),
                    datasets: [{
                        label: 'Quantidade de Atestados',
                        data: top5Setores.map(d => d.quantidade),
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
                                    const setor = top5Setores[index];
                                    return [
                                        `Atestados: ${setor.quantidade || 0}`,
                                        `Dias perdidos: ${setor.dias_perdidos || 0}`,
                                        `Horas perdidas: ${setor.horas_perdidas || 0}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            ticks: { font: { size: 11 }, stepSize: 1 }
                        },
                        x: { 
                            ticks: { 
                                font: { size: 11 },
                                maxRotation: 0,
                                autoSkip: false
                            }
                        }
                    }
                }
            };
            break;
            
        case 'genero':
            const totalGenero = dados.reduce((sum, d) => sum + (d.quantidade || 0), 0);
            config = {
                type: 'doughnut',
                data: {
                    labels: dados.map(d => d.genero === 'M' ? 'Masculino' : 'Feminino'),
                    datasets: [{
                        data: dados.map(d => d.quantidade || 0),
                        backgroundColor: [CORES_EMPRESA.primary, CORES_EMPRESA.secondary]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true, 
                            position: 'bottom',
                            labels: { font: { size: 11 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const item = dados[index];
                                    const pct = totalGenero > 0 ? ((item.quantidade || 0) / totalGenero * 100).toFixed(1) : 0;
                                    return [
                                        `${item.genero === 'M' ? 'Masculino' : 'Feminino'}: ${item.quantidade || 0} atestados`,
                                        `Percentual: ${pct}%`
                                    ];
                                }
                            }
                        }
                    }
                }
            };
            break;
            
        case 'dias_doenca':
            const top5Cids = dados.slice(0, 5);
            config = {
                type: 'bar',
                data: {
                    labels: top5Cids.map(d => truncate(d.descricao || d.cid, 18)),
                    datasets: [{
                        label: 'Dias',
                        data: top5Cids.map(d => d.dias_perdidos),
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
            };
            break;
            
        case 'escalas':
            const top10Escalas = dados.slice(0, 10);
            config = {
                type: 'bar',
                data: {
                    labels: top10Escalas.map(d => d.escala || 'N/A'),
                    datasets: [{
                        label: 'Atestados',
                        data: top10Escalas.map(d => d.quantidade || 0),
                        backgroundColor: PALETA_EMPRESA
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const escala = top10Escalas[index];
                                    return `Atestados: ${escala.quantidade || 0}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { beginAtZero: true },
                        y: {
                            ticks: {
                                font: { size: 11 },
                                maxRotation: 0,
                                autoSkip: false
                            }
                        }
                    }
                }
            };
            break;
            
        case 'motivos':
            const top10Motivos = dados.slice(0, 10);
            const totalMotivos = top10Motivos.reduce((sum, m) => sum + (m.quantidade || 0), 0);
            config = {
                type: 'pie',
                data: {
                    labels: top10Motivos.map(d => d.motivo || 'N/A'),
                    datasets: [{
                        data: top10Motivos.map(d => d.quantidade || 0),
                        backgroundColor: PALETA_EMPRESA
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true, 
                            position: 'right',
                            labels: {
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    if (data.labels.length && data.datasets.length) {
                                        return data.labels.map((label, i) => {
                                            const dataset = data.datasets[0];
                                            const motivo = top10Motivos[i];
                                            const quantidade = motivo.quantidade || 0;
                                            const percentual = totalMotivos > 0 ? ((quantidade / totalMotivos) * 100).toFixed(1) : 0;
                                            return {
                                                text: `${label} - ${percentual}% (${quantidade})`,
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
                                    const motivo = top10Motivos[index];
                                    const quantidade = motivo.quantidade || 0;
                                    const percentual = totalMotivos > 0 ? ((quantidade / totalMotivos) * 100).toFixed(1) : 0;
                                    return [
                                        `Motivo: ${motivo.motivo || 'N/A'}`,
                                        `Quantidade: ${quantidade} atestados`,
                                        `Percentual: ${percentual}%`
                                    ];
                                }
                            }
                        }
                    }
                }
            };
            break;
            
        case 'centro_custo':
            const top10Setores = dados.slice(0, 10);
            config = {
                type: 'bar',
                data: {
                    labels: top10Setores.map(d => truncate(d.centro_custo || d.setor || 'N/A', 25)),
                    datasets: [{
                        label: 'Dias Perdidos',
                        data: top10Setores.map(d => d.dias_perdidos || 0),
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
                                    const item = top10Setores[index];
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
            };
            break;
            
        case 'distribuicao_dias':
            config = {
                type: 'bar',
                data: {
                    labels: dados.map(d => `${d.faixa || d.dias || 'N/A'}`),
                    datasets: [{
                        label: 'Quantidade',
                        data: dados.map(d => d.quantidade || 0),
                        backgroundColor: CORES_EMPRESA.primaryLight
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const item = dados[index];
                                    return `Quantidade: ${item.quantidade || 0} atestados`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: { beginAtZero: true },
                        x: { ticks: { font: { size: 11 } } }
                    }
                }
            };
            break;
            
        case 'media_cid':
            const top10MediaCid = dados.slice(0, 10);
            config = {
                type: 'bar',
                data: {
                    labels: top10MediaCid.map(d => truncate(d.cid + ' - ' + (d.diagnostico || d.descricao || ''), 30)),
                    datasets: [{
                        label: 'Média de Dias',
                        data: top10MediaCid.map(d => d.media_dias || 0),
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
                                    const item = top10MediaCid[index];
                                    return [
                                        `Média: ${item.media_dias || 0} dias`,
                                        `Total de dias: ${item.total_dias || 0}`,
                                        `Quantidade: ${item.quantidade || 0} atestados`,
                                        `Diagnóstico: ${item.diagnostico || item.descricao || 'N/A'}`
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
            };
            break;
            
        case 'setor_genero':
            // Calcula total geral para calcular percentuais
            const totalGeralSetorGenero = dados.reduce((sum, d) => sum + (d.dias_perdidos || 0), 0);
            
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
            
            const setoresLabels = setoresOrdenados.map(s => s.setor);
            const generos = ['M', 'F'];
            // Azul Marinho para Masculino, Verde Oliva para Feminino
            const cores = { 'M': CORES_EMPRESA.primary, 'F': CORES_EMPRESA.secondary };
            
            // Prepara dados com percentuais
            const datasetsSetorGenero = generos.map(genero => {
                const label = genero === 'M' ? 'Masculino' : 'Feminino';
                const data = setoresLabels.map(setor => {
                    const item = setoresOrdenados.find(s => s.setor === setor);
                    return item ? (item[genero] || 0) : 0;
                });
                
                // Calcula percentuais para tooltip
                const percentuais = data.map(valor => {
                    return totalGeralSetorGenero > 0 ? ((valor / totalGeralSetorGenero) * 100).toFixed(2) : '0.00';
                });
                
                return {
                    label: label,
                    data: data,
                    backgroundColor: cores[genero],
                    borderRadius: 6,
                    percentuais: percentuais
                };
            });
            
            config = {
                type: 'bar',
                data: {
                    labels: setoresLabels.map(s => truncate(s, 25)),
                    datasets: datasetsSetorGenero
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
                                    const percentualSetor = totalGeralSetorGenero > 0 ? ((totalSetor / totalGeralSetorGenero) * 100).toFixed(2) : '0.00';
                                    
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
            };
            break;
    }
    
    if (config.type) {
        charts['chartSlide'] = new Chart(ctx, config);
    }
}

// ==================== NAVEGAÇÃO ====================
function proximoSlide() {
    if (slideAtual < slides.length - 1) {
        slideAtual++;
        renderizarSlide(slides[slideAtual]);
        atualizarBotoes();
    }
}

function slideAnterior() {
    if (slideAtual > 0) {
        slideAtual--;
        renderizarSlide(slides[slideAtual]);
        atualizarBotoes();
    }
}

function atualizarBotoes() {
    document.getElementById('btnPrev').disabled = slideAtual === 0;
    document.getElementById('btnNext').disabled = slideAtual === slides.length - 1;
}

function sairApresentacao() {
    if (confirm('Deseja sair da apresentação?')) {
        window.location.href = '/';
    }
}

// ==================== RENDERIZAR SLIDES DE AÇÕES ====================
function renderizarAcoesIntro(tipo) {
    // Carrega conteúdo salvo do localStorage
    const conteudoSalvo = localStorage.getItem(`acoes_${tipo}`);
    const dados = conteudoSalvo ? JSON.parse(conteudoSalvo) : {
        texto: "INTERVENÇÕES JUNTO<br>AOS COLABORADORES"
    };
    
    return `
        <div style="display: flex; flex-direction: column; height: 100%; padding: 40px; padding-bottom: 70px;">
            <!-- Linha decorativa no topo -->
            <div style="height: 3px; background: linear-gradient(to right, #6B8E23 0%, #1a237e 50%, #6B8E23 100%); margin-bottom: 30px;"></div>
            
            <div style="flex: 1; display: flex; align-items: center; justify-content: center; position: relative; min-height: 500px;">
                <!-- Texto editável centralizado -->
                <div style="text-align: center; background: linear-gradient(135deg, #6B8E23, #556B2F); color: white; padding: 60px 80px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.25); border: 3px solid rgba(255,255,255,0.2); max-width: 800px;">
                    <div id="textoAcoesIntro" class="conteudo-editavel" contenteditable="false" style="font-size: 40px; font-weight: 700; margin: 0; line-height: 1.4; outline: none; min-height: 90px; text-shadow: 0 2px 4px rgba(0,0,0,0.2); letter-spacing: 2px;">${dados.texto}</div>
                </div>
            </div>
        </div>
    `;
}

function renderizarFooterAcoes() {
    return `
        <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 60px; display: flex; align-items: flex-end; justify-content: flex-end; padding: 0 40px 8px 40px; gap: 20px;">
            <!-- Barra gradiente que vai até o limite do nome -->
            <div style="flex: 1; height: 32px; background: linear-gradient(to right, #6B8E23 0%, #1a237e 50%, #6B8E23 100%); margin-right: 20px; margin-bottom: 0;"></div>
            
            <!-- Logo Conver no fundo branco (à direita, acima da barra) -->
            <div style="display: flex; align-items: center; gap: 0; flex-shrink: 0; margin-bottom: 0;">
                <span style="font-size: 48px; font-weight: 700; color: #1a237e; letter-spacing: 1px; line-height: 1;">C</span>
                <div style="width: 46px; height: 46px; position: relative; display: inline-flex; align-items: center; justify-content: center; margin: 0 2px;">
                    <svg width="46" height="46" viewBox="0 0 46 46">
                        <circle cx="23" cy="23" r="20" fill="none" stroke="#6B8E23" stroke-width="3"/>
                        <path d="M 23 7 A 16 16 0 1 1 21 39" fill="none" stroke="#1a237e" stroke-width="2.5" stroke-linecap="round"/>
                        <circle cx="23" cy="9" r="2.5" fill="#6B8E23"/>
                    </svg>
                </div>
                <span style="font-size: 48px; font-weight: 700; color: #1a237e; letter-spacing: 1px; line-height: 1;">NVER</span>
            </div>
        </div>
    `;
}

function renderizarAcoesSaudeFisica(tipo) {
    // Carrega conteúdo salvo do localStorage
    const conteudoSalvo = localStorage.getItem(`acoes_${tipo}`);
    const dados = conteudoSalvo ? JSON.parse(conteudoSalvo) : {
        texto: "A saúde deve ser compreendida, primordialmente, como uma responsabilidade individual. Nesse sentido, este eixo tem como foco a promoção da saúde preventiva, por meio da disseminação de informações, orientações e ações que estimulem a adoção de hábitos saudáveis. Busca-se, assim, fortalecer o autocuidado e proporcionar uma melhoria contínua na qualidade de vida, abaixo algumas ações:",
        acoes: [
            "Alimentação saudável;",
            "Atividade Física;",
            "Qualidade do sono;",
            "Comportamento preventivo e cuidados médicos/saúde;",
            "Álcool e tabagismo;",
            "Exames periódicos;",
            "Programa de acompanhamento e monitoramento em saúde;",
            "Grupos de interesse;",
            "Campanhas de vacinação, segurança no trabalho e afastamento;"
        ]
    };
    
    const acoesHTML = dados.acoes.map(acao => `
        <li class="acao-item" style="padding: 12px 0; padding-left: 30px; position: relative; font-size: 16px; line-height: 1.8; color: #333; border-bottom: 1px solid #f0f0f0;">
            <span style="position: absolute; left: 0; color: #6B8E23; font-weight: bold;">•</span>
            <span class="conteudo-editavel" contenteditable="false" style="outline: none;">${acao}</span>
        </li>
    `).join('');
    
    return `
        <div style="display: flex; flex-direction: column; height: 100%; padding: 40px; padding-bottom: 70px;">
            <!-- Linha decorativa no topo -->
            <div style="height: 3px; background: linear-gradient(to right, #6B8E23 0%, #1a237e 50%, #6B8E23 100%); margin-bottom: 30px;"></div>
            
            <!-- Tabs -->
            <div style="display: flex; gap: 8px; margin-bottom: 30px; border-bottom: 3px solid #6B8E23;">
                <div style="background: #6B8E23; color: white; padding: 12px 24px; border-radius: 8px 8px 0 0; font-weight: 600; font-size: 14px;">
                    SAÚDE FÍSICA
                </div>
                <div style="background: white; color: #1a237e; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE EMOCIONAL
                </div>
                <div style="background: white; color: #1a237e; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE SOCIAL
                </div>
            </div>
            
            <!-- Conteúdo -->
            <div style="flex: 1; overflow-y: auto; padding-right: 20px;">
                <p class="conteudo-editavel" id="textoAcoesSaudeFisica" contenteditable="false" style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 30px; text-align: justify; outline: none; min-height: 100px;">${dados.texto}</p>
                
                <ul id="listaAcoesSaudeFisica" style="list-style: none; padding: 0; margin: 0;">
                    ${acoesHTML}
                </ul>
            </div>
        </div>
    `;
}

function renderizarAcoesSaudeEmocional(tipo) {
    // Carrega conteúdo salvo do localStorage
    const conteudoSalvo = localStorage.getItem(`acoes_${tipo}`);
    const dados = conteudoSalvo ? JSON.parse(conteudoSalvo) : {
        texto: "A saúde emocional refere-se à capacidade de gerenciar sentimentos, enfrentar desafios e manter o equilíbrio psicológico. Este eixo visa promover o bem-estar emocional através de ações que fortaleçam a resiliência, a inteligência emocional e o suporte psicossocial. Abaixo algumas ações:",
        acoes: [
            "Gestão do estresse e ansiedade;",
            "Programas de mindfulness e relaxamento;",
            "Acompanhamento psicológico e suporte emocional;",
            "Treinamento em inteligência emocional;",
            "Espaços de escuta e acolhimento;",
            "Prevenção e combate ao assédio moral;",
            "Balanceamento entre vida pessoal e profissional;",
            "Programas de desenvolvimento pessoal;",
            "Campanhas de conscientização sobre saúde mental;"
        ]
    };
    
    const acoesHTML = dados.acoes.map(acao => `
        <li class="acao-item" style="padding: 12px 0; padding-left: 30px; position: relative; font-size: 16px; line-height: 1.8; color: #333; border-bottom: 1px solid #f0f0f0;">
            <span style="position: absolute; left: 0; color: #6B8E23; font-weight: bold;">•</span>
            <span class="conteudo-editavel" contenteditable="false" style="outline: none;">${acao}</span>
        </li>
    `).join('');
    
    return `
        <div style="display: flex; flex-direction: column; height: 100%; padding: 40px; padding-bottom: 70px;">
            <!-- Linha decorativa no topo -->
            <div style="height: 3px; background: linear-gradient(to right, #6B8E23 0%, #1a237e 50%, #6B8E23 100%); margin-bottom: 30px;"></div>
            
            <!-- Tabs -->
            <div style="display: flex; gap: 8px; margin-bottom: 30px; border-bottom: 3px solid #6B8E23;">
                <div style="background: white; color: #1a237e; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE FÍSICA
                </div>
                <div style="background: #6B8E23; color: white; padding: 12px 24px; border-radius: 8px 8px 0 0; font-weight: 600; font-size: 14px;">
                    SAÚDE EMOCIONAL
                </div>
                <div style="background: white; color: #1a237e; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE SOCIAL
                </div>
            </div>
            
            <!-- Conteúdo -->
            <div style="flex: 1; overflow-y: auto; padding-right: 20px;">
                <p class="conteudo-editavel" id="textoAcoesSaudeEmocional" contenteditable="false" style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 30px; text-align: justify; outline: none; min-height: 100px;">${dados.texto}</p>
                
                <ul id="listaAcoesSaudeEmocional" style="list-style: none; padding: 0; margin: 0;">
                    ${acoesHTML}
                </ul>
            </div>
        </div>
    `;
}

function renderizarAcoesSaudeSocial(tipo) {
    // Carrega conteúdo salvo do localStorage
    const conteudoSalvo = localStorage.getItem(`acoes_${tipo}`);
    const dados = conteudoSalvo ? JSON.parse(conteudoSalvo) : {
        texto: "A saúde social está relacionada à qualidade das relações interpessoais, à integração no ambiente de trabalho e à construção de um ambiente colaborativo e respeitoso. Este eixo busca fortalecer os vínculos sociais e promover um clima organizacional saudável. Abaixo algumas ações:",
        acoes: [
            "Programas de integração e acolhimento;",
            "Atividades de team building;",
            "Comunicação eficaz e transparente;",
            "Resolução de conflitos;",
            "Valorização da diversidade e inclusão;",
            "Eventos sociais e culturais;",
            "Grupos de trabalho colaborativos;",
            "Programas de reconhecimento e valorização;",
            "Espaços de convivência e interação;"
        ]
    };
    
    const acoesHTML = dados.acoes.map(acao => `
        <li class="acao-item" style="padding: 12px 0; padding-left: 30px; position: relative; font-size: 16px; line-height: 1.8; color: #333; border-bottom: 1px solid #f0f0f0;">
            <span style="position: absolute; left: 0; color: #6B8E23; font-weight: bold;">•</span>
            <span class="conteudo-editavel" contenteditable="false" style="outline: none;">${acao}</span>
        </li>
    `).join('');
    
    return `
        <div style="display: flex; flex-direction: column; height: 100%; padding: 40px; padding-bottom: 70px;">
            <!-- Linha decorativa no topo -->
            <div style="height: 3px; background: linear-gradient(to right, #6B8E23 0%, #1a237e 50%, #6B8E23 100%); margin-bottom: 30px;"></div>
            
            <!-- Tabs -->
            <div style="display: flex; gap: 8px; margin-bottom: 30px; border-bottom: 3px solid #6B8E23;">
                <div style="background: white; color: #1a237e; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE FÍSICA
                </div>
                <div style="background: white; color: #1a237e; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE EMOCIONAL
                </div>
                <div style="background: #6B8E23; color: white; padding: 12px 24px; border-radius: 8px 8px 0 0; font-weight: 600; font-size: 14px;">
                    SAÚDE SOCIAL
                </div>
            </div>
            
            <!-- Conteúdo -->
            <div style="flex: 1; overflow-y: auto; padding-right: 20px;">
                <p class="conteudo-editavel" id="textoAcoesSaudeSocial" contenteditable="false" style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 30px; text-align: justify; outline: none; min-height: 100px;">${dados.texto}</p>
                
                <ul id="listaAcoesSaudeSocial" style="list-style: none; padding: 0; margin: 0;">
                    ${acoesHTML}
                </ul>
            </div>
        </div>
    `;
}

// ==================== PRODUTIVIDADE ====================
function renderizarProdutividade(slide) {
    const dados = slide.dados || [];
    
    if (!dados || dados.length === 0) {
        return '<div class="empty-state"><p>Nenhum dado de produtividade disponível</p></div>';
    }
    
    // Calcula totais por categoria
    const totais = {
        ocupacionais: dados.reduce((sum, d) => sum + (d.ocupacionais || 0), 0),
        assistenciais: dados.reduce((sum, d) => sum + (d.assistenciais || 0), 0),
        acidente_trabalho: dados.reduce((sum, d) => sum + (d.acidente_trabalho || 0), 0),
        inss: dados.reduce((sum, d) => sum + (d.inss || 0), 0),
        absenteismo: dados.reduce((sum, d) => sum + (d.absenteismo || 0), 0),
        total: dados.reduce((sum, d) => sum + (d.total || 0), 0)
    };
    
    // Carrega configurações
    const config = JSON.parse(localStorage.getItem('produtividade_apresentacao') || '{}');
    
    // Determina layout baseado nos gráficos ativos
    const graficosAtivos = [];
    if (config.graficoCategoria?.ativo !== false) graficosAtivos.push('categoria');
    if (config.graficoTipo?.ativo !== false) graficosAtivos.push('tipo');
    if (config.graficoEvolucao?.ativo === true) graficosAtivos.push('evolucao');
    
    if (graficosAtivos.length === 0) {
        return '<div class="empty-state"><p>Nenhum gráfico configurado para exibição</p></div>';
    }
    
    let html = '';
    
    // Layout responsivo baseado na quantidade de gráficos
    if (graficosAtivos.length === 1) {
        html = `<div style="display: flex; justify-content: center; align-items: center; height: 100%;">`;
        if (graficosAtivos.includes('categoria')) {
            html += `<div style="width: 80%; max-width: 800px;"><canvas id="chartProdutividadeCategorias"></canvas></div>`;
        } else if (graficosAtivos.includes('tipo')) {
            html += `<div style="width: 80%; max-width: 800px;"><canvas id="chartProdutividadeTipos"></canvas></div>`;
        } else if (graficosAtivos.includes('evolucao')) {
            html += `<div style="width: 100%;"><canvas id="graficoEvolucaoProdutividade"></canvas></div>`;
        }
        html += `</div>`;
    } else if (graficosAtivos.length === 2) {
        html = `<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; height: 100%;">`;
        if (graficosAtivos.includes('categoria')) {
            html += `<div><canvas id="chartProdutividadeCategorias"></canvas></div>`;
        }
        if (graficosAtivos.includes('tipo')) {
            html += `<div><canvas id="chartProdutividadeTipos"></canvas></div>`;
        }
        if (graficosAtivos.includes('evolucao')) {
            html += `<div style="grid-column: 1 / -1;"><canvas id="graficoEvolucaoProdutividade"></canvas></div>`;
        }
        html += `</div>`;
    } else {
        html = `<div style="display: flex; flex-direction: column; gap: 24px; height: 100%;">`;
        if (graficosAtivos.includes('categoria') || graficosAtivos.includes('tipo')) {
            html += `<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">`;
            if (graficosAtivos.includes('categoria')) {
                html += `<div><canvas id="chartProdutividadeCategorias"></canvas></div>`;
            }
            if (graficosAtivos.includes('tipo')) {
                html += `<div><canvas id="chartProdutividadeTipos"></canvas></div>`;
            }
            html += `</div>`;
        }
        if (graficosAtivos.includes('evolucao')) {
            html += `<div style="flex: 1; min-height: 300px;"><canvas id="graficoEvolucaoProdutividade"></canvas></div>`;
        }
        html += `</div>`;
    }
    
    // Renderiza gráficos após o HTML ser inserido
    setTimeout(() => {
        renderizarGraficoProdutividade(dados, totais);
    }, 100);
    
    return html;
}

function renderizarGraficoProdutividade(dados, totais) {
    // Carrega configurações
    const config = JSON.parse(localStorage.getItem('produtividade_apresentacao') || '{}');
    
    // Gráfico de categorias
    if (config.graficoCategoria?.ativo !== false) {
        const ctxCategorias = document.getElementById('chartProdutividadeCategorias');
        if (ctxCategorias && !charts['produtividade_categorias']) {
            const tipoGrafico = config.graficoCategoria?.tipo || 'bar';
            
            const configChart = {
                type: tipoGrafico,
                data: {
                    labels: ['Ocupacionais', 'Assistenciais', 'Acidente de Trabalho', 'INSS', 'Absenteísmo'],
                    datasets: [{
                        label: 'Total de Consultas',
                        data: [
                            totais.ocupacionais,
                            totais.assistenciais,
                            totais.acidente_trabalho,
                            totais.inss,
                            totais.absenteismo
                        ],
                        backgroundColor: [
                            CORES_EMPRESA.primary,
                            CORES_EMPRESA.secondary,
                            '#ff9800',
                            '#9c27b0',
                            '#f44336'
                        ],
                        borderColor: [
                            CORES_EMPRESA.primaryDark,
                            CORES_EMPRESA.secondaryDark,
                            '#f57c00',
                            '#7b1fa2',
                            '#c62828'
                        ],
                        borderRadius: tipoGrafico === 'bar' ? 6 : 0,
                        borderWidth: tipoGrafico === 'pie' || tipoGrafico === 'doughnut' ? 2 : 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: tipoGrafico === 'pie' || tipoGrafico === 'doughnut' || tipoGrafico === 'radar',
                            position: 'bottom'
                        }
                    },
                    scales: tipoGrafico !== 'pie' && tipoGrafico !== 'doughnut' && tipoGrafico !== 'radar' ? {
                        y: { beginAtZero: true }
                    } : undefined
                }
            };
            
            charts['produtividade_categorias'] = new Chart(ctxCategorias, configChart);
        }
    }
    
    // Gráfico de tipos
    if (config.graficoTipo?.ativo !== false) {
        const ctxTipos = document.getElementById('chartProdutividadeTipos');
        if (ctxTipos && !charts['produtividade_tipos']) {
            const tipos = dados.map(d => d.tipo_consulta || d.numero_tipo || 'N/A');
            const totaisTipos = dados.map(d => d.total || 0);
            const tipoGrafico = config.graficoTipo?.tipo || 'doughnut';
            
            const configChart = {
                type: tipoGrafico,
                data: {
                    labels: tipos,
                    datasets: [{
                        label: 'Total',
                        data: totaisTipos,
                        backgroundColor: PALETA_EMPRESA
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    },
                    scales: tipoGrafico === 'bar' || tipoGrafico === 'line' ? {
                        y: { beginAtZero: true }
                    } : undefined
                }
            };
            
            charts['produtividade_tipos'] = new Chart(ctxTipos, configChart);
        }
    }
    
    // Gráfico de evolução mensal (se ativado)
    if (config.graficoEvolucao?.ativo === true) {
        renderizarGraficoEvolucaoMensal(config.graficoEvolucao?.tipo || 'line');
    }
}

function renderizarGraficoEvolucaoMensal(tipoGrafico) {
    // Busca dados dos últimos 12 meses usando a nova API
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (!clientId) return;
    
    fetch(`/api/produtividade/evolucao?client_id=${clientId}&agrupar_por=mes`)
        .then(response => response.json())
        .then(data => {
            const dadosAgregados = data.data || [];
            
            // Pega últimos 12 meses
            const dadosRecentes = dadosAgregados.slice(-12);
            
            // Formata labels
            const meses = {
                '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
                '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
                '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
            };
            
            const labels = dadosRecentes.map(d => {
                if (d.periodo && d.periodo.includes('-')) {
                    const [ano, mes] = d.periodo.split('-');
                    return `${meses[mes] || mes}/${ano.slice(-2)}`;
                }
                return d.periodo;
            });
            
            const dadosEvolucao = {
                ocupacionais: dadosRecentes.map(d => d.ocupacionais || 0),
                assistenciais: dadosRecentes.map(d => d.assistenciais || 0),
                acidente_trabalho: dadosRecentes.map(d => d.acidente_trabalho || 0),
                inss: dadosRecentes.map(d => d.inss || 0),
                absenteismo: dadosRecentes.map(d => d.absenteismo || 0),
                total: dadosRecentes.map(d => d.total || 0)
            };
            
            setTimeout(() => {
                const ctx = document.getElementById('graficoEvolucaoProdutividade');
                if (ctx && !charts['produtividade_evolucao']) {
                    const isArea = tipoGrafico === 'area';
                    charts['produtividade_evolucao'] = new Chart(ctx, {
                        type: isArea ? 'line' : tipoGrafico,
                        data: {
                            labels: labels,
                            datasets: [
                                {
                                    label: 'Ocupacionais',
                                    data: dadosEvolucao.ocupacionais,
                                    borderColor: CORES_EMPRESA.primary,
                                    backgroundColor: isArea ? 'rgba(26, 35, 126, 0.2)' : CORES_EMPRESA.primary,
                                    fill: isArea,
                                    tension: 0.4
                                },
                                {
                                    label: 'Assistenciais',
                                    data: dadosEvolucao.assistenciais,
                                    borderColor: CORES_EMPRESA.secondary,
                                    backgroundColor: isArea ? 'rgba(85, 107, 47, 0.2)' : CORES_EMPRESA.secondary,
                                    fill: isArea,
                                    tension: 0.4
                                },
                                {
                                    label: 'Acidente de Trabalho',
                                    data: dadosEvolucao.acidente_trabalho,
                                    borderColor: '#ff9800',
                                    backgroundColor: isArea ? 'rgba(255, 152, 0, 0.2)' : '#ff9800',
                                    fill: isArea,
                                    tension: 0.4
                                },
                                {
                                    label: 'INSS',
                                    data: dadosEvolucao.inss,
                                    borderColor: '#9c27b0',
                                    backgroundColor: isArea ? 'rgba(156, 39, 176, 0.2)' : '#9c27b0',
                                    fill: isArea,
                                    tension: 0.4
                                },
                                {
                                    label: 'Absenteísmo',
                                    data: dadosEvolucao.absenteismo,
                                    borderColor: '#f44336',
                                    backgroundColor: isArea ? 'rgba(244, 67, 54, 0.2)' : '#f44336',
                                    fill: isArea,
                                    tension: 0.4
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                }
                            },
                            scales: {
                                y: { beginAtZero: true }
                            }
                        }
                    });
                }
            }, 100);
        })
        .catch(error => {
            console.error('Erro ao carregar dados de evolução:', error);
        });
}

// ==================== EDIÇÃO DE AÇÕES ====================
let modoEdicaoAcoes = false;

function toggleEdicaoAcoes(tipo) {
    modoEdicaoAcoes = !modoEdicaoAcoes;
    const editaveis = document.querySelectorAll('.conteudo-editavel');
    const btnEditar = document.getElementById('btnEditarAcoes');
    const btnSalvar = document.getElementById('btnSalvarAcoes');
    
    editaveis.forEach(el => {
        el.contentEditable = modoEdicaoAcoes;
        if (modoEdicaoAcoes) {
            el.style.border = '2px dashed #556B2F';
            el.style.borderRadius = '4px';
            el.style.padding = '4px';
            el.style.backgroundColor = '#f9f9f9';
        } else {
            el.style.border = 'none';
            el.style.padding = '0';
            el.style.backgroundColor = 'transparent';
        }
    });
    
    if (modoEdicaoAcoes) {
        btnEditar.style.display = 'none';
        btnSalvar.style.display = 'flex';
    } else {
        btnEditar.style.display = 'flex';
        btnSalvar.style.display = 'none';
    }
}

function salvarAcoes(tipo) {
    const dados = {};
    
    if (tipo === 'acoes_intro') {
        const textoEl = document.getElementById('textoAcoesIntro');
        if (textoEl) {
            dados.texto = textoEl.innerHTML;
        }
    } else {
        // Para os outros slides (saude_fisica, saude_emocional, saude_social)
        const textoEl = document.querySelector(`#textoAcoes${tipo.replace('acoes_', '').split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')}`);
        const acoesItems = document.querySelectorAll(`#listaAcoes${tipo.replace('acoes_', '').split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')} .acao-item .conteudo-editavel`);
        
        if (textoEl) {
            dados.texto = textoEl.innerHTML;
        }
        
        if (acoesItems.length > 0) {
            dados.acoes = Array.from(acoesItems).map(item => item.textContent.trim());
        }
    }
    
    // Salva no localStorage
    localStorage.setItem(`acoes_${tipo}`, JSON.stringify(dados));
    
    // Desativa modo de edição
    toggleEdicaoAcoes(tipo);
    
    // Mostra mensagem de sucesso
    const btnSalvar = document.getElementById('btnSalvarAcoes');
    const textoOriginal = btnSalvar.innerHTML;
    btnSalvar.innerHTML = '<i class="fas fa-check"></i> Salvo!';
    btnSalvar.style.background = '#28a745';
    
    setTimeout(() => {
        btnSalvar.innerHTML = textoOriginal;
        btnSalvar.style.background = '#1a237e';
    }, 2000);
}

// ==================== UTILITÁRIOS ====================
function truncate(str, maxLen) {
    if (!str) return 'N/A';
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

function formatarAnalise(texto) {
    if (!texto) return 'Análise não disponível.';
    
    // Converte **texto** para <strong>texto</strong>
    texto = texto.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Converte quebras de linha para <br>
    texto = texto.replace(/\n/g, '<br>');
    
    return texto;
}

function mostrarErro(mensagem) {
    const container = document.getElementById('slideContent');
    container.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Erro</h3>
            <p>${mensagem}</p>
        </div>
    `;
}

