// ==================== VARIÁVEIS GLOBAIS ====================
// Funções para obter cores do cliente (carregadas dinamicamente)
function getCores() {
    if (typeof getCoresCliente === 'function') {
        return getCoresCliente();
    }
    // Fallback para cores padrão
    return {
        primary: '#1a237e',
        primaryDark: '#0d47a1',
        primaryLight: '#3949ab',
        primaryLighter: '#5c6bc0',
        primaryDarkest: '#000051',
        secondary: '#556B2F',
        secondaryDark: '#4a5d23',
        secondaryLight: '#6B8E23',
        secondaryLighter: '#808000',
        gray: '#9E9E9E',
        grayLight: '#BDBDBD',
        grayDark: '#757575',
        masculino: '#1a237e',
        feminino: '#556B2F'
    };
}

function getPaleta() {
    if (typeof getPaletaCliente === 'function') {
        return getPaletaCliente();
    }
    // Fallback para paleta padrão
    return ['#1a237e', '#556B2F', '#0d47a1', '#6B8E23', '#3949ab', '#808000', '#5c6bc0', '#4a5d23', '#9E9E9E', '#757575'];
}

// Função auxiliar para obter cores da RODA DE OURO (preto e cinza)
function getCoresRodaOuro() {
    return {
        preto: '#000000',
        cinza: '#808080',
        cinzaEscuro: '#404040',
        cinzaClaro: '#A0A0A0'
    };
}

// Função para criar gradiente preto-cinza
function criarGradientePretoCinza(ctx, area) {
    const gradient = ctx.createLinearGradient(0, area.top, 0, area.bottom);
    gradient.addColorStop(0, '#000000'); // Preto no topo
    gradient.addColorStop(1, '#808080'); // Cinza na base
    return gradient;
}

// Mantém compatibilidade com código existente
const CORES_EMPRESA = new Proxy({}, {
    get: (target, prop) => {
        const cores = getCores();
        return cores[prop] || cores.primary;
    }
});

const PALETA_EMPRESA = new Proxy([], {
    get: (target, prop) => {
        const paleta = getPaleta();
        if (prop === 'slice') {
            return (...args) => paleta.slice(...args);
        }
        if (prop === 'length') {
            return paleta.length;
        }
        if (typeof prop === 'string' && !isNaN(prop)) {
            return paleta[parseInt(prop)];
        }
        return paleta[prop];
    }
});

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
    // Carrega cores do cliente primeiro
    if (typeof carregarCoresCliente === 'function') {
        const clientId = getClientId();
        if (clientId) {
            await carregarCoresCliente(clientId);
        }
    }
    
    await carregarFiltros();
    
    // Aplica cor dourada ao Dashboard se for Roda de Ouro
    aplicarCorDashboardRodaOuro();
    
    carregarDashboard();
});

// Função para aplicar cor dourada ao Dashboard quando for Roda de Ouro
function aplicarCorDashboardRodaOuro() {
    const clientId = getClientId();
    const currentPath = window.location.pathname;
    const isDashboardPage = currentPath === '/' || currentPath === '/index.html';
    
    if (clientId === 4 && isDashboardPage) {
        // Encontra o item Dashboard no menu
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            const span = item.querySelector('.nav-item-title') || item.querySelector('span');
            const href = item.getAttribute('href');
            if ((span && span.textContent.trim() === 'Dashboard') || (href === '/' || href === '/index.html')) {
                item.classList.add('active', 'roda-ouro-dashboard');
            }
        });
        
        // Também verifica pelo ID
        const navDashboard = document.getElementById('navDashboard');
        if (navDashboard) {
            navDashboard.classList.add('active', 'roda-ouro-dashboard');
        }
    } else {
        // Remove a classe se não for Roda de Ouro ou não estiver no dashboard
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            if (item.classList.contains('roda-ouro-dashboard')) {
                item.classList.remove('roda-ouro-dashboard');
            }
        });
    }
}

// Observa mudanças no cliente selecionado
if (typeof window.addEventListener !== 'undefined') {
    window.addEventListener('storage', (e) => {
        if (e.key === 'cliente_selecionado') {
            setTimeout(aplicarCorDashboardRodaOuro, 100);
        }
    });
    
    // Observa mudanças quando o cliente é alterado
    const originalSetItem = localStorage.setItem;
    localStorage.setItem = function(key, value) {
        originalSetItem.apply(this, arguments);
        if (key === 'cliente_selecionado') {
            setTimeout(aplicarCorDashboardRodaOuro, 100);
        }
    };
}

// ==================== HELPER FUNCTIONS ====================

function garantirClientId(clientId, endpoint = '') {
    /**
     * Garante que client_id seja sempre válido antes de fazer requisições
     * Retorna o client_id válido ou lança erro
     */
    if (!clientId || clientId <= 0) {
        const errorMsg = `client_id é obrigatório para ${endpoint || 'esta requisição'}. Selecione um cliente primeiro.`;
        console.error(`[CLIENT_ID] ${errorMsg}`);
        throw new Error(errorMsg);
    }
    console.log(`[CLIENT_ID] Usando client_id: ${clientId} para ${endpoint || 'requisição'}`);
    return clientId;
}

// ==================== CARREGAR DASHBOARD ====================
let camposDisponiveis = {}; // Armazena campos disponíveis do cliente atual

// Função para limpar TODOS os dados do dashboard ao trocar de cliente
function limparTodosDadosDashboard() {
    console.log('[ISOLAMENTO] Limpando TODOS os dados do dashboard...');
    
    // Limpa campos disponíveis
    camposDisponiveis = { mapeados: {}, com_dados: [], custom_fields: [] };
    
    // Limpa alertas
    if (window.alertasData) {
        window.alertasData = [];
    }
    
    // LIMPA INSIGHTS (ISOLAMENTO)
    const insightsContainer = document.getElementById('insightsContainer');
    const insightsSection = document.getElementById('insightsSection');
    if (insightsContainer) {
        insightsContainer.innerHTML = '';
        console.log('[ISOLAMENTO] Insights container limpo');
    }
    if (insightsSection) {
        insightsSection.style.display = 'none';
    }
    
    // Destrói TODOS os gráficos Chart.js (busca por padrão)
    Object.keys(window).forEach(key => {
        if (key.startsWith('chart') && window[key] && typeof window[key].destroy === 'function') {
            try {
                window[key].destroy();
                window[key] = null;
            } catch (e) {
                console.warn(`[ISOLAMENTO] Erro ao destruir gráfico ${key}:`, e);
            }
        }
    });
    
    // Limpa variáveis globais de gráficos
    chartCids = null;
    chartSetores = null;
    chartEvolucao = null;
    chartGenero = null;
    chartMediaCid = null;
    chartFuncionariosDias = null;
    chartEscalas = null;
    chartMotivos = null;
    chartCentroCusto = null;
    chartDistribuicaoDias = null;
    chartMediaCidDias = null;
    chartEvolucaoSetor = null;
    chartComparativoDiasHoras = null;
    chartFrequenciaAtestados = null;
    chartSetorGenero = null;
    chartProdutividade = null;
    chartProdutividadeEvolucao = null;
    chartProdutividadeMensalCategoria = null;
    
    // Gráficos de horas perdidas (Roda de Ouro)
    if (window.chartHorasPerdidasGenero) {
        try { window.chartHorasPerdidasGenero.destroy(); } catch(e) {}
        window.chartHorasPerdidasGenero = null;
    }
    if (window.chartHorasPerdidasSetor) {
        try { window.chartHorasPerdidasSetor.destroy(); } catch(e) {}
        window.chartHorasPerdidasSetor = null;
    }
    if (window.chartEvolucaoMensalHoras) {
        try { window.chartEvolucaoMensalHoras.destroy(); } catch(e) {}
        window.chartEvolucaoMensalHoras = null;
    }
    if (window.chartComparativoDiasHorasGenero) {
        try { window.chartComparativoDiasHorasGenero.destroy(); } catch(e) {}
        window.chartComparativoDiasHorasGenero = null;
    }
    if (window.chartHorasPerdidasSetorGenero) {
        try { window.chartHorasPerdidasSetorGenero.destroy(); } catch(e) {}
        window.chartHorasPerdidasSetorGenero = null;
    }
    if (window.chartAnaliseDetalhadaGenero) {
        try { window.chartAnaliseDetalhadaGenero.destroy(); } catch(e) {}
        window.chartAnaliseDetalhadaGenero = null;
    }
    
    console.log('[ISOLAMENTO] Todos os dados limpos');
}

async function carregarCamposDisponiveis(clientId) {
    try {
        const response = await fetch(`/api/clientes/${clientId}/campos-disponiveis`);
        if (response.ok) {
            const data = await response.json();
            camposDisponiveis = {
                mapeados: data.campos_mapeados || {},
                com_dados: data.campos_com_dados || [],
                custom_fields: data.custom_fields || []
            };
            console.log('📊 Campos disponíveis carregados:', camposDisponiveis);
        }
    } catch (error) {
        console.error('Erro ao carregar campos disponíveis:', error);
        camposDisponiveis = { mapeados: {}, com_dados: [], custom_fields: [] };
    }
}

function temCampo(campo) {
    const resultado = camposDisponiveis.com_dados && camposDisponiveis.com_dados.includes(campo);
    console.log(`[DEBUG] temCampo('${campo}') = ${resultado}`, camposDisponiveis);
    return resultado;
}

async function carregarDashboard() {
    try {
        const clientId = getClientId();
        
        // Se não tem cliente selecionado, não carrega (silenciosamente)
        if (!clientId || clientId <= 0) {
            console.log('[DASHBOARD] Aguardando seleção de cliente...');
            return;
        }
        
        // LIMPA TODOS OS DADOS ANTES DE CARREGAR NOVOS (ISOLAMENTO TOTAL)
        limparTodosDadosDashboard();
        
        // LIMPA INSIGHTS ANTES DE CARREGAR NOVOS (ISOLAMENTO)
        const insightsContainer = document.getElementById('insightsContainer');
        const insightsSection = document.getElementById('insightsSection');
        if (insightsContainer) {
            insightsContainer.innerHTML = '';
        }
        if (insightsSection) {
            insightsSection.style.display = 'none';
        }

        // Carrega campos disponíveis primeiro
        await carregarCamposDisponiveis(clientId);

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
        
        console.log('[DEBUG] Dados recebidos do dashboard:', {
            top_cids: data.top_cids?.length || 0,
            top_setores: data.top_setores?.length || 0,
            top_funcionarios: data.top_funcionarios?.length || 0,
            evolucao_mensal: data.evolucao_mensal?.length || 0,
            produtividade: data.produtividade?.length || 0,
            camposDisponiveis: camposDisponiveis
        });
        
        // Renderiza cards (a função renderizarCards já verifica se há dados)
        renderizarCards(data.metricas || {});
        
        // ISOLAMENTO: Mostra/oculta gráficos da Converplast baseado em client_id
        const converplastClientId = clientId ? parseInt(clientId) : null;
        console.log('[DEBUG] clientId recebido:', clientId, '| converplastClientId:', converplastClientId);
        
        // Aguarda um pouco para garantir que o DOM está pronto
        setTimeout(() => {
            const secaoConverplast = document.getElementById('graficosConverplast');
            console.log('[DEBUG] Elemento graficosConverplast encontrado:', !!secaoConverplast);
            
            if (secaoConverplast) {
                // Só mostra se for Converplast (ID 2)
                if (converplastClientId === 2) {
                    secaoConverplast.style.display = 'block';
                    console.log('[ISOLAMENTO] ✅ Mostrando gráficos Converplast - clientId:', converplastClientId);
                } else {
                    secaoConverplast.style.display = 'none';
                    console.log('[ISOLAMENTO] ❌ Ocultando gráficos Converplast - clientId:', converplastClientId, '(não é Converplast)');
                }
            } else {
                console.error('[ISOLAMENTO] ⚠️ ERRO: Elemento graficosConverplast não encontrado no DOM!');
            }
        }, 100);
        
        // Armazena alertas para o menu (não renderiza aqui)
        window.alertasData = data.alertas || [];
        if (typeof carregarAlertasMenu === 'function') {
            carregarAlertasMenu();
        }
        
        // Renderiza insights
        renderizarInsights(data.insights || []);
        
        // Renderiza gráficos SEMPRE que houver dados (ignora temCampo para garantir que funcione)
        // Gráficos de CID
        if (data.top_cids && data.top_cids.length > 0) {
            console.log('[DEBUG] Renderizando gráficos de CID com', data.top_cids.length, 'itens');
            renderizarChartCids(data.top_cids);
            renderizarChartMediaCid(data.top_cids);
        }
        if (data.media_cid && data.media_cid.length > 0) {
            renderizarChartMediaCidDias(data.media_cid);
        }
        
        // Gráficos de Setor
        if (data.top_setores && data.top_setores.length > 0) {
            console.log('[DEBUG] Renderizando gráficos de Setor com', data.top_setores.length, 'itens');
            renderizarChartSetores(data.top_setores);
        }
        if (data.evolucao_setor && Object.keys(data.evolucao_setor).length > 0) {
            renderizarChartEvolucaoSetor(data.evolucao_setor);
        }
        if (data.dias_setor_genero && data.dias_setor_genero.length > 0) {
            renderizarChartSetorGenero(data.dias_setor_genero);
        }
        
        // Gráfico de Evolução
        if (data.evolucao_mensal && data.evolucao_mensal.length > 0) {
            console.log('[DEBUG] Renderizando gráfico de Evolução com', data.evolucao_mensal.length, 'itens');
            renderizarChartEvolucao(data.evolucao_mensal);
        }
        
        // Gráfico de Gênero
        if (data.distribuicao_genero && data.distribuicao_genero.length > 0) {
            renderizarChartGenero(data.distribuicao_genero);
        }
        
        // Gráfico de Funcionários
        if (data.top_funcionarios && data.top_funcionarios.length > 0) {
            console.log('[DEBUG] Renderizando gráficos de Funcionários com', data.top_funcionarios.length, 'itens');
            renderizarChartFuncionariosDias(data.top_funcionarios);
        }
        if (data.frequencia_atestados && data.frequencia_atestados.length > 0) {
            renderizarChartFrequenciaAtestados(data.frequencia_atestados);
        }
        
        // Gráfico de Escalas
        if (data.top_escalas && data.top_escalas.length > 0) {
            renderizarChartEscalas(data.top_escalas);
        }
        
        // Gráfico de Motivos
        if (data.top_motivos && data.top_motivos.length > 0) {
            renderizarChartMotivos(data.top_motivos);
        }
        
        // Gráfico de Centro de Custo
        if (data.dias_centro_custo && data.dias_centro_custo.length > 0) {
            renderizarChartCentroCusto(data.dias_centro_custo);
        }
        
        // Gráficos de Dias/Horas
        if (data.distribuicao_dias && data.distribuicao_dias.length > 0) {
            renderizarChartDistribuicaoDias(data.distribuicao_dias);
        }
        if (data.comparativo_dias_horas && data.comparativo_dias_horas.length > 0) {
            renderizarChartComparativoDiasHoras(data.comparativo_dias_horas);
        }
        
        // Gráficos de Produtividade
        if (data.produtividade && data.produtividade.length > 0) {
            console.log('[DEBUG] Renderizando gráficos de Produtividade com', data.produtividade.length, 'itens');
            renderizarChartProdutividade(data.produtividade);
            renderizarChartProdutividadeMensalCategoria(data.produtividade);
        }
        
        // Carrega evolução de produtividade separadamente
        await carregarEvolucaoProdutividade();
        
        // Renderiza gráficos específicos da Roda de Ouro (APENAS para client_id = 4)
        const rodaOuroClientId = clientId ? parseInt(clientId) : null;
        if (rodaOuroClientId === 4 && (data.classificacao_funcionarios_ro || data.classificacao_setores_ro)) {
            // Mostra seção de gráficos da Roda de Ouro
            const secaoRodaOuro = document.getElementById('graficosRodaOuro');
            if (secaoRodaOuro) {
                secaoRodaOuro.style.display = 'block';
            }
            
            // Renderiza os 6 gráficos
            renderizarChartClassificacaoFuncionariosRO(data.classificacao_funcionarios_ro || []);
            renderizarChartClassificacaoSetoresRO(data.classificacao_setores_ro || []);
            renderizarChartDiasAnoCoerencia(data.dias_ano_coerencia || {});
            renderizarChartClassificacaoDoencasRO(data.classificacao_doencas_ro || []);
            renderizarChartAnaliseCoerencia(data.analise_coerencia || {});
            renderizarChartTempoServicoAtestados(data.tempo_servico_atestados || []);
            
            // Novos gráficos de horas perdidas
            if (data.horas_perdidas_genero && data.horas_perdidas_genero.length > 0) {
                renderizarChartHorasPerdidasGenero(data.horas_perdidas_genero);
            }
            if (data.horas_perdidas_setor && data.horas_perdidas_setor.length > 0) {
                renderizarChartHorasPerdidasSetor(data.horas_perdidas_setor);
            }
            if (data.evolucao_mensal_horas && data.evolucao_mensal_horas.length > 0) {
                renderizarChartEvolucaoMensalHoras(data.evolucao_mensal_horas);
            }
            if (data.comparativo_dias_horas_genero && data.comparativo_dias_horas_genero.length > 0) {
                renderizarChartComparativoDiasHorasGenero(data.comparativo_dias_horas_genero);
            }
            if (data.horas_perdidas_setor_genero && data.horas_perdidas_setor_genero.length > 0) {
                renderizarChartHorasPerdidasSetorGenero(data.horas_perdidas_setor_genero);
            }
            if (data.analise_detalhada_genero && data.analise_detalhada_genero.generos && data.analise_detalhada_genero.generos.length > 0) {
                renderizarChartAnaliseDetalhadaGenero(data.analise_detalhada_genero);
            }
        } else {
            // Oculta seção se não for Roda de Ouro (client_id != 4)
            const secaoRodaOuro = document.getElementById('graficosRodaOuro');
            if (secaoRodaOuro) {
                secaoRodaOuro.style.display = 'none';
            }
        }
        
        // Comparativo entre períodos (todos os clientes)
        if (data.comparativo_periodos_mes && Object.keys(data.comparativo_periodos_mes).length > 0) {
            renderizarChartComparativoMensal(data.comparativo_periodos_mes);
        }
        if (data.comparativo_periodos_trimestre && Object.keys(data.comparativo_periodos_trimestre).length > 0) {
            renderizarChartComparativoTrimestral(data.comparativo_periodos_trimestre);
        }
        
        // Carrega e renderiza gráficos personalizados configurados pelo usuário
        await carregarERenderizarGraficosPersonalizados(clientId);
        
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        alert('Erro ao carregar dados. Verifique se o servidor está funcionando.');
    }
}

// ==================== GRÁFICOS PERSONALIZADOS ====================

let graficosPersonalizadosInstances = {}; // Armazena instâncias dos gráficos personalizados

async function carregarERenderizarGraficosPersonalizados(clientId) {
    try {
        console.log('📊 Carregando gráficos personalizados para cliente:', clientId);
        
        // Busca gráficos configurados
        const response = await fetch(`/api/clientes/${clientId}/graficos`);
        if (!response.ok) {
            console.warn('⚠️ Erro ao buscar gráficos:', response.status);
            return;
        }
        
        const data = await response.json();
        const graficos = data.graficos || [];
        
        console.log('📈 Gráficos encontrados:', graficos.length, graficos);
        
        if (graficos.length === 0) {
            console.log('ℹ️ Nenhum gráfico configurado para este cliente');
            return;
        }
        
        // Remove gráficos personalizados anteriores
        const containerPersonalizados = document.getElementById('graficosPersonalizadosContainer');
        if (containerPersonalizados) {
            containerPersonalizados.remove();
        }
        
        // Cria container para gráficos personalizados
        const mainContent = document.querySelector('.main-content');
        if (!mainContent) return;
        
        const container = document.createElement('div');
        container.id = 'graficosPersonalizadosContainer';
        container.style.marginTop = '32px';
        container.style.paddingTop = '32px';
        container.style.borderTop = '2px solid var(--border)';
        
        const tituloSecao = document.createElement('div');
        tituloSecao.style.marginBottom = '24px';
        tituloSecao.innerHTML = `
            <h2 style="font-size: 24px; font-weight: 600; color: var(--text-primary); margin: 0;">
                <i class="fas fa-chart-bar" style="margin-right: 8px;"></i>Gráficos Personalizados
            </h2>
            <p style="font-size: 14px; color: var(--text-secondary); margin: 8px 0 0 0;">
                Análises configuradas especificamente para esta empresa
            </p>
        `;
        container.appendChild(tituloSecao);
        
        // Cria grid para gráficos
        const grid = document.createElement('div');
        grid.style.display = 'grid';
        grid.style.gridTemplateColumns = 'repeat(2, 1fr)';
        grid.style.gap = '16px';
        grid.id = 'graficosPersonalizadosGrid';
        container.appendChild(grid);
        
        mainContent.appendChild(container);
        
        // Renderiza cada gráfico
        for (let i = 0; i < graficos.length; i++) {
            const grafico = graficos[i];
            await renderizarGraficoPersonalizado(grafico, i, clientId);
        }
        
    } catch (error) {
        console.error('Erro ao carregar gráficos personalizados:', error);
    }
}

async function renderizarGraficoPersonalizado(config, index, clientId) {
    try {
        console.log(`🎨 Renderizando gráfico ${index + 1}/${graficos.length}:`, config.titulo);
        
        // Gera dados do gráfico
        const response = await fetch(`/api/clientes/${clientId}/graficos/gerar-dados`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`❌ Erro ao gerar dados do gráfico ${config.titulo}:`, response.status, errorText);
            return;
        }
        
        const data = await response.json();
        console.log(`📦 Dados recebidos para ${config.titulo}:`, data);
        
        if (!data.success) {
            console.warn(`⚠️ Gráfico ${config.titulo} retornou erro:`, data.detail || 'Erro desconhecido');
            return;
        }
        
        if (!data.labels || data.labels.length === 0) {
            console.warn(`⚠️ Gráfico ${config.titulo} não tem dados`);
            return;
        }
        
        console.log(`✅ Renderizando gráfico ${config.titulo} com ${data.labels.length} itens`);
        
        // Cria container do gráfico
        const grid = document.getElementById('graficosPersonalizadosGrid');
        if (!grid) return;
        
        const chartCard = document.createElement('div');
        chartCard.className = 'chart-container';
        chartCard.id = `graficoPersonalizado_${index}`;
        
        chartCard.innerHTML = `
            <div class="chart-header">
                <h3 class="chart-title">${config.titulo || 'Gráfico'}</h3>
                ${config.descricao ? `<p class="chart-subtitle">${config.descricao}</p>` : ''}
            </div>
            <div class="chart-wrapper" style="height: 350px;">
                <canvas id="canvasGraficoPersonalizado_${index}"></canvas>
            </div>
        `;
        
        grid.appendChild(chartCard);
        
        // Aguarda um pouco para o DOM atualizar
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Renderiza gráfico com Chart.js
        const canvas = document.getElementById(`canvasGraficoPersonalizado_${index}`);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destrói gráfico anterior se existir
        if (graficosPersonalizadosInstances[`grafico_${index}`]) {
            graficosPersonalizadosInstances[`grafico_${index}`].destroy();
        }
        
        // Decide qual dado usar (valores numéricos ou quantidades)
        const camposNumericos = ['dias_atestados', 'horas_perdi', 'numero_dias_atestado', 'horas_perdidas', 'dias_perdidos'];
        const temCampoNumerico = camposNumericos.includes(config.campo) || 
                                 (config.campos_agrupar && config.campos_agrupar.some(c => camposNumericos.includes(c)));
        const dadosParaGrafico = temCampoNumerico && data.valores && data.valores.length > 0 && data.valores.some(v => v > 0) 
                                 ? data.valores 
                                 : data.quantidades;
        
        // Configuração base do gráfico
        const chartConfig = {
            data: {
                labels: data.labels,
                datasets: [{
                    label: config.titulo,
                    data: dadosParaGrafico,
                    backgroundColor: getPaleta().slice(0, data.labels.length),
                    borderColor: getCores().primary,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: config.tipo === 'pie' || config.tipo === 'doughnut',
                        position: 'bottom'
                    },
                    tooltip: {
                        enabled: true
                    }
                }
            }
        };
        
        // Ajusta configuração baseado no tipo
        if (config.tipo === 'bar-horizontal') {
            chartConfig.type = 'bar';
            chartConfig.options.indexAxis = 'y';
        } else if (config.tipo === 'line') {
            chartConfig.type = 'line';
            chartConfig.data.datasets[0].fill = false;
            chartConfig.data.datasets[0].tension = 0.4;
        } else if (config.tipo === 'pie') {
            chartConfig.type = 'pie';
        } else if (config.tipo === 'doughnut') {
            chartConfig.type = 'doughnut';
        } else if (config.tipo === 'area') {
            chartConfig.type = 'line';
            chartConfig.data.datasets[0].fill = true;
        } else {
            chartConfig.type = 'bar';
        }
        
        // Cria instância do gráfico
        graficosPersonalizadosInstances[`grafico_${index}`] = new Chart(ctx, chartConfig);
        
    } catch (error) {
        console.error(`Erro ao renderizar gráfico personalizado ${config.titulo}:`, error);
    }
}


// ==================== RENDERIZAR CARDS ====================
function ocultarGrafico(chartId) {
    const chartContainer = document.getElementById(chartId)?.closest('.chart-container')?.closest('.chart-card');
    if (chartContainer) {
        chartContainer.style.display = 'none';
    }
}

function renderizarCards(metricas) {
    const diasPerdidos = metricas.total_dias_perdidos || 0;
    const horasPerdidas = metricas.total_horas_perdidas || 0;
    const totalRegistros = metricas.total_registros || 0;
    
    // Encontra o container dos cards
    const cardsContainer = document.querySelector('.cards-grid');
    
    // Se não houver dados REAIS, oculta os cards
    if (diasPerdidos === 0 && horasPerdidas === 0 && totalRegistros === 0) {
        if (cardsContainer) {
            cardsContainer.style.display = 'none';
        }
        return;
    }
    
    // TEM DADOS - Mostra e preenche os cards
    if (cardsContainer) {
        cardsContainer.style.display = 'grid';
    }
    
    // Dias Perdidos = Soma da coluna DIAS ATESTADOS
    const elDiasPerdidos = document.getElementById('cardDiasPerdidos');
    if (elDiasPerdidos) {
        elDiasPerdidos.textContent = Math.round(diasPerdidos).toLocaleString('pt-BR');
    }
    
    // Horas Perdidas = Soma da coluna HORAS PERDI
    const elHorasPerdidas = document.getElementById('cardHorasPerdidas');
    if (elHorasPerdidas) {
        elHorasPerdidas.textContent = Math.round(horasPerdidas).toLocaleString('pt-BR');
    }
}

// ==================== RENDERIZAR INSIGHTS ====================
function renderizarInsights(insights) {
    const container = document.getElementById('insightsContainer');
    const section = document.getElementById('insightsSection');
    
    // LIMPA SEMPRE ANTES DE RENDERIZAR (ISOLAMENTO)
    if (container) {
        container.innerHTML = '';
    }
    
    const clientId = getClientId();
    console.log(`[INSIGHTS] Renderizando insights para client_id=${clientId}, quantidade: ${insights?.length || 0}`);
    
    if (!insights || insights.length === 0) {
        if (section) section.style.display = 'none';
        console.log(`[INSIGHTS] Nenhum insight para client_id=${clientId}, ocultando seção`);
        return;
    }
    
    if (section) section.style.display = 'block';
    
    if (container) {
        // Log dos insights que estão sendo renderizados
        insights.forEach((insight, index) => {
            console.log(`[INSIGHTS] Insight ${index + 1} para client_id=${clientId}: ${insight.titulo}`);
        });
        
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

// Função helper para destruir gráfico de forma segura
function destruirGraficoSeguro(canvasId, variavelGlobal) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    // Destrói variável global se existir e for um Chart válido
    if (variavelGlobal) {
        try {
            // Verifica se é um objeto Chart válido
            if (variavelGlobal && typeof variavelGlobal.destroy === 'function') {
                variavelGlobal.destroy();
            }
        } catch (e) {
            console.warn(`Erro ao destruir ${canvasId} (variável):`, e);
        }
    }
    
    // Verifica se há gráfico no canvas (Chart.js pode ter criado um)
    const existingChart = Chart.getChart(canvas);
    if (existingChart) {
        try {
            existingChart.destroy();
        } catch (e) {
            console.warn(`Erro ao destruir ${canvasId} (canvas):`, e);
        }
    }
}

function renderizarChartCids(dados) {
    const ctx = document.getElementById('chartCids');
    if (!ctx || !dados || dados.length === 0) return;
    
    destruirGraficoSeguro('chartCids', chartCids);
    chartCids = null;
    
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
    
    destruirGraficoSeguro('chartSetores', chartSetores);
    chartSetores = null;
    
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
    
    destruirGraficoSeguro('chartEvolucao', chartEvolucao);
    chartEvolucao = null;
    
    chartEvolucao = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dados.map(d => d.mes || 'N/A'),
            datasets: [
                {
                    label: 'Dias Perdidos',
                    data: dados.map(d => d.dias_perdidos || 0),
                    borderColor: CORES_EMPRESA.primary,
                    backgroundColor: (CORES_EMPRESA.primaryLight || CORES_EMPRESA.primary) + '40',
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Quantidade de Atestados',
                    data: dados.map(d => d.quantidade || 0),
                    borderColor: CORES_EMPRESA.secondary,
                    backgroundColor: (CORES_EMPRESA.secondaryLight || CORES_EMPRESA.secondary) + '40',
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
                legend: { display: true, position: 'top' }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    type: 'linear',
                    display: true,
                    position: 'left',
                },
                y1: {
                    beginAtZero: true,
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        }
    });
}

function renderizarChartGenero(dados) {
    const ctx = document.getElementById('chartGenero');
    if (!ctx || !dados || dados.length === 0) return;
    
    destruirGraficoSeguro('chartGenero', chartGenero);
    chartGenero = null;
    
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
    
    destruirGraficoSeguro('chartMediaCid', chartMediaCid);
    chartMediaCid = null;
    
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
    
    destruirGraficoSeguro('chartFuncionariosDias', chartFuncionariosDias);
    chartFuncionariosDias = null;
    
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
    
    destruirGraficoSeguro('chartEscalas', chartEscalas);
    chartEscalas = null;
    
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
    
    destruirGraficoSeguro('chartMotivos', chartMotivos);
    chartMotivos = null;
    
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
    
    destruirGraficoSeguro('chartCentroCusto', chartCentroCusto);
    chartCentroCusto = null;
    
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
    
    destruirGraficoSeguro('chartDistribuicaoDias', chartDistribuicaoDias);
    chartDistribuicaoDias = null;
    
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
    
    destruirGraficoSeguro('chartMediaCidDias', chartMediaCidDias);
    chartMediaCidDias = null;
    
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
    
    destruirGraficoSeguro('chartEvolucaoSetor', chartEvolucaoSetor);
    chartEvolucaoSetor = null;
    
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
    
    destruirGraficoSeguro('chartComparativoDiasHoras', chartComparativoDiasHoras);
    chartComparativoDiasHoras = null;
    
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
    
    destruirGraficoSeguro('chartFrequenciaAtestados', chartFrequenciaAtestados);
    chartFrequenciaAtestados = null;
    
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
    
    destruirGraficoSeguro('chartProdutividade', chartProdutividade);
    chartProdutividade = null;
    
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
    
    // Determina o período (anos disponíveis)
    const meses = Object.keys(dadosPorMes).sort();
    let periodoTexto = '';
    if (meses.length > 0) {
        // Extrai anos únicos
        const anos = [...new Set(meses.map(m => m.split('-')[0]))].sort();
        if (anos.length === 1) {
            periodoTexto = `Ano ${anos[0]} (Mês a Mês)`;
        } else if (anos.length > 1) {
            periodoTexto = `Anos ${anos[0]} a ${anos[anos.length - 1]} (Mês a Mês)`;
        }
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
                    backgroundColor: getCores().primary || '#0056b3',
                    borderRadius: { topLeft: 6, topRight: 6, bottomLeft: 0, bottomRight: 0 }
                },
                {
                    label: 'Faltas',
                    data: dataFaltas,
                    backgroundColor: getCores().secondary || '#dc3545',
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
    
    destruirGraficoSeguro('chartProdutividadeMensalCategoria', chartProdutividadeMensalCategoria);
    chartProdutividadeMensalCategoria = null;
    
    // Agrupa por mês (dados anuais mês a mês)
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
    
    // Gera gradiente de cores baseado nas cores do cliente
    const cores = getCores();
    const paleta = getPaleta();
    
    // Cria gradiente do primary ao secondary
    const categorias = [
        { nome: 'Ocupacionais', key: 'ocupacionais', cor: cores.primary },
        { nome: 'Assistenciais', key: 'assistenciais', cor: cores.primaryLight },
        { nome: 'Acidente de Trabalho', key: 'acidente_trabalho', cor: cores.primaryLighter },
        { nome: 'INSS', key: 'inss', cor: paleta[3] || cores.secondaryLight },
        { nome: 'Sinistralidade', key: 'sinistralidade', cor: paleta[4] || cores.secondary },
        { nome: 'Absenteísmo', key: 'absenteismo', cor: cores.secondary },
        { nome: 'Perícia Indireta', key: 'pericia_indireta', cor: cores.secondaryDark }
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
        
        // Busca dados agregados por mês (dados anuais mês a mês)
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
    
    destruirGraficoSeguro('chartProdutividadeEvolucao', chartProdutividadeEvolucao);
    chartProdutividadeEvolucao = null;
    
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
    
    destruirGraficoSeguro('chartSetorGenero', chartSetorGenero);
    chartSetorGenero = null;
    
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

// ==================== GRÁFICOS RODA DE OURO ====================

function renderizarChartClassificacaoFuncionariosRO(dados) {
    if (!dados || dados.length === 0) {
        const canvas = document.getElementById('chartClassificacaoFuncionariosRO');
        if (canvas && canvas.parentElement) {
            canvas.parentElement.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">Nenhum dado disponível</div>';
        }
        return;
    }
    
    const ctx = document.getElementById('chartClassificacaoFuncionariosRO');
    if (!ctx) return;
    
    // Destrói gráfico anterior se existir
    if (window.chartClassificacaoFuncionariosRO && typeof window.chartClassificacaoFuncionariosRO.destroy === 'function') {
        window.chartClassificacaoFuncionariosRO.destroy();
    }
    
    const cores = getCores();
    const paleta = getPaleta();
    const coresRO = getCoresRodaOuro();
    
    // Ordena por quantidade (decrescente) e pega top 15
    const dadosOrdenados = [...dados].sort((a, b) => (b.quantidade || 0) - (a.quantidade || 0)).slice(0, 15);
    
    window.chartClassificacaoFuncionariosRO = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dadosOrdenados.map(d => {
                // Trunca nome se muito longo
                const nome = d.nome || 'Não informado';
                return nome.length > 20 ? nome.substring(0, 17) + '...' : nome;
            }),
            datasets: [{
                label: 'Dias de Atestados',
                data: dadosOrdenados.map(d => d.quantidade || 0),
                backgroundColor: function(context) {
                    // Gradiente preto-cinza para este gráfico (horizontal)
                    const chart = context.chart;
                    const {ctx, chartArea} = chart;
                    if (!chartArea) return coresRO.preto;
                    return criarGradientePretoCinza(ctx, chartArea);
                },
                borderColor: coresRO.preto,
                borderWidth: 1
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
                        label: function(context) {
                            return `Dias de Atestados: ${context.parsed.x}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: '#f0f0f0'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function renderizarChartClassificacaoSetoresRO(dados) {
    if (!dados || dados.length === 0) {
        const canvas = document.getElementById('chartClassificacaoSetoresRO');
        if (canvas && canvas.parentElement) {
            canvas.parentElement.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">Nenhum dado disponível</div>';
        }
        return;
    }
    
    const ctx = document.getElementById('chartClassificacaoSetoresRO');
    if (!ctx) return;
    
    // Destrói gráfico anterior se existir
    if (window.chartClassificacaoSetoresRO && typeof window.chartClassificacaoSetoresRO.destroy === 'function') {
        window.chartClassificacaoSetoresRO.destroy();
    }
    
    const cores = getCores();
    const paleta = getPaleta();
    const coresRO = getCoresRodaOuro();
    
    // Ordena por dias_afastamento (decrescente) e pega top 15
    const dadosOrdenados = [...dados].sort((a, b) => (b.dias_afastamento || 0) - (a.dias_afastamento || 0)).slice(0, 15);
    
    window.chartClassificacaoSetoresRO = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dadosOrdenados.map(d => d.setor || 'Não informado'),
            datasets: [{
                label: 'Dias de Afastamento',
                data: dadosOrdenados.map(d => Math.round(d.dias_afastamento || 0)),
                backgroundColor: coresRO.cinza, // Cinza sólido para diferenciar do gráfico anterior
                borderColor: coresRO.cinzaEscuro,
                borderWidth: 1
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
                        label: function(context) {
                            return `Dias de Afastamento: ${context.parsed.x}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: '#f0f0f0'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function renderizarChartDiasAnoCoerencia(dados) {
    // Usa dados mensais se disponíveis, senão usa dados anuais
    const usarDadosMensais = dados.meses && dados.meses.length > 0;
    const labels = usarDadosMensais ? dados.meses : (dados.anos || []);
    const dadosCoerente = usarDadosMensais ? dados.coerente_mensal : (dados.coerente || []);
    const dadosSemCoerencia = usarDadosMensais ? dados.sem_coerencia_mensal : (dados.sem_coerencia || []);
    
    if (!labels || labels.length === 0) {
        const canvas = document.getElementById('chartDiasAnoCoerencia');
        if (canvas && canvas.parentElement) {
            canvas.parentElement.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">Nenhum dado disponível</div>';
        }
        return;
    }
    
    const ctx = document.getElementById('chartDiasAnoCoerencia');
    if (!ctx) return;
    
    destruirGraficoSeguro('chartDiasAnoCoerencia', window.chartDiasAnoCoerencia);
    window.chartDiasAnoCoerencia = null;
    
    const cores = getCores();
    const paleta = getPaleta();
    const coresRO = getCoresRodaOuro();
    
    // Formata labels (se for mês-ano, formata melhor)
    const labelsFormatados = labels.map(label => {
        if (label.includes('-') && label.length === 7) {
            // Formato YYYY-MM
            const [ano, mes] = label.split('-');
            const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
            const mesNum = parseInt(mes) - 1;
            return `${meses[mesNum]}/${ano}`;
        }
        return label;
    });
    
    window.chartDiasAnoCoerencia = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labelsFormatados,
            datasets: [
                {
                    label: 'Coerente',
                    data: dadosCoerente,
                    backgroundColor: coresRO.preto, // Preto
                    borderColor: coresRO.preto,
                    borderWidth: 1
                },
                {
                    label: 'Sem Coerência',
                    data: dadosSemCoerencia,
                    backgroundColor: coresRO.cinza, // Cinza
                    borderColor: coresRO.cinzaEscuro,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} dias`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    grid: {
                        display: false
                    }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    grid: {
                        color: '#f0f0f0'
                    }
                }
            }
        }
    });
}

function renderizarChartClassificacaoDoencasRO(dados) {
    console.log('📊 renderizarChartClassificacaoDoencasRO - Dados recebidos:', dados);
    
    if (!dados || dados.length === 0) {
        const canvas = document.getElementById('chartClassificacaoDoencasRO');
        if (canvas && canvas.parentElement) {
            const wrapper = canvas.closest('.chart-wrapper');
            if (wrapper) {
                wrapper.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">Nenhum dado disponível</div>';
            }
        }
        return;
    }
    
    const ctx = document.getElementById('chartClassificacaoDoencasRO');
    if (!ctx) {
        console.error('❌ Canvas chartClassificacaoDoencasRO não encontrado');
        return;
    }
    
    destruirGraficoSeguro('chartClassificacaoDoencasRO', window.chartClassificacaoDoencasRO);
    window.chartClassificacaoDoencasRO = null;
    
    const cores = getCores();
    const paleta = getPaleta();
    const coresRO = getCoresRodaOuro();
    
    // Ordena por quantidade (decrescente) e pega top 15
    const dadosOrdenados = [...dados].sort((a, b) => (b.quantidade || 0) - (a.quantidade || 0)).slice(0, 15);
    
    console.log('📊 Dados ordenados (top 15):', dadosOrdenados);
    
    window.chartClassificacaoDoencasRO = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dadosOrdenados.map(d => {
                // Trunca nome da doença se muito longo
                const nome = d.tipo_doenca || 'Não informado';
                return nome.length > 20 ? nome.substring(0, 17) + '...' : nome;
            }),
            datasets: [{
                label: 'Dias de Afastamento',
                data: dadosOrdenados.map(d => d.quantidade || 0),
                backgroundColor: function(context) {
                    // Gradiente preto-cinza para este gráfico (vertical)
                    const chart = context.chart;
                    const {ctx, chartArea} = chart;
                    if (!chartArea) return coresRO.preto;
                    const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                    gradient.addColorStop(0, '#000000'); // Preto na base
                    gradient.addColorStop(1, '#808080'); // Cinza no topo
                    return gradient;
                },
                borderColor: coresRO.preto,
                borderWidth: 1
            }]
        },
        options: {
            // Barras verticais (colunas)
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            // Mostra o nome completo da doença no título do tooltip
                            const index = context[0].dataIndex;
                            return dadosOrdenados[index].tipo_doenca || 'Não informado';
                        },
                        label: function(context) {
                            return `Dias de Afastamento: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f0f0f0'
                    },
                    title: {
                        display: true,
                        text: 'Dias de Afastamento'
                    }
                }
            }
        }
    });
}

function renderizarChartAnaliseCoerencia(dados) {
    if (!dados || dados.total === 0) {
        const canvas = document.getElementById('chartAnaliseCoerencia');
        if (canvas && canvas.parentElement) {
            canvas.parentElement.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">Nenhum dado disponível</div>';
        }
        return;
    }
    
    const ctx = document.getElementById('chartAnaliseCoerencia');
    if (!ctx) return;
    
    // Destrói gráfico anterior se existir
    if (window.chartAnaliseCoerencia && typeof window.chartAnaliseCoerencia.destroy === 'function') {
        window.chartAnaliseCoerencia.destroy();
    }
    
    const cores = getCores();
    const paleta = getPaleta();
    const coresRO = getCoresRodaOuro();
    
    const coerente = dados.coerente || 0;
    const semCoerencia = dados.sem_coerencia || 0;
    const total = dados.total || 0;
    const percentualCoerente = dados.percentual_coerente || 0;
    const percentualSemCoerencia = dados.percentual_sem_coerencia || 0;
    
    window.chartAnaliseCoerencia = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Coerente', 'Sem Coerência'],
            datasets: [{
                data: [coerente, semCoerencia],
                backgroundColor: [coresRO.preto, coresRO.cinza], // Preto e cinza
                borderColor: ['#fff', '#fff'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const percent = total > 0 ? ((value / total) * 100).toFixed(2) : 0;
                            return `${label}: ${value} dias (${percent}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Adiciona texto no centro do donut
    const chartContainer = ctx.parentElement;
    if (chartContainer) {
        const centerText = document.createElement('div');
        centerText.id = 'centerTextAnaliseCoerencia';
        centerText.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; pointer-events: none;';
        centerText.innerHTML = `
            <div style="font-size: 24px; font-weight: 600; color: #333;">${total}</div>
            <div style="font-size: 12px; color: #666;">Total dias</div>
        `;
        chartContainer.style.position = 'relative';
        if (!document.getElementById('centerTextAnaliseCoerencia')) {
            chartContainer.appendChild(centerText);
        }
    }
}

function renderizarChartTempoServicoAtestados(dados) {
    // Novo formato: array com faixas de tempo de serviço
    if (!dados || !Array.isArray(dados) || dados.length === 0) {
        const canvas = document.getElementById('chartTempoServicoAtestados');
        if (canvas && canvas.parentElement) {
            canvas.parentElement.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">Nenhum dado disponível</div>';
        }
        return;
    }
    
    const ctx = document.getElementById('chartTempoServicoAtestados');
    if (!ctx) return;
    
    destruirGraficoSeguro('chartTempoServicoAtestados', window.chartTempoServicoAtestados);
    window.chartTempoServicoAtestados = null;
    
    const cores = getCores();
    const paleta = getPaleta();
    const coresRO = getCoresRodaOuro();
    
    // Extrai labels (faixas de tempo) e dados (dias de afastamento)
    const labels = dados.map(d => d.faixa_tempo_servico || 'Não informado');
    const dadosDias = dados.map(d => d.dias_afastamento || 0);
    
    window.chartTempoServicoAtestados = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Dias de Afastamento',
                data: dadosDias,
                backgroundColor: coresRO.preto, // Preto sólido para este gráfico
                borderColor: coresRO.preto,
                borderWidth: 1
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
                        label: function(context) {
                            const index = context.dataIndex;
                            const item = dados[index];
                            return [
                                `Dias de Afastamento: ${item.dias_afastamento || 0}`,
                                `Quantidade de Atestados: ${item.quantidade_atestados || 0}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f0f0f0'
                    },
                    title: {
                        display: true,
                        text: 'Dias de Afastamento'
                    }
                }
            }
        }
    });
}

// ==================== GRÁFICOS DE HORAS PERDIDAS (RODA DE OURO) ====================

function renderizarChartHorasPerdidasGenero(dados) {
    const ctx = document.getElementById('chartHorasPerdidasGenero');
    if (!ctx || !dados || dados.length === 0) return;
    
    destruirGraficoSeguro('chartHorasPerdidasGenero', window.chartHorasPerdidasGenero);
    window.chartHorasPerdidasGenero = null;
    
    const cores = getCores();
    // Cor dourada para feminino: #FFD700 (gold)
    const coresGenero = dados.map(d => d.genero === 'M' ? cores.masculino : '#FFD700');
    
    window.chartHorasPerdidasGenero = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: dados.map(d => `${d.genero_label} (${d.semanas_perdidas.toFixed(1)} semanas)`),
            datasets: [{
                label: 'Horas Perdidas',
                data: dados.map(d => d.horas_perdidas),
                backgroundColor: coresGenero,
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
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const dataIndex = context.dataIndex;
                            const semanas = dados[dataIndex]?.semanas_perdidas || 0;
                            return `${label}: ${value.toFixed(1)}h (${semanas.toFixed(1)} semanas)`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Horas Perdidas por Gênero',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 20 }
                }
            }
        }
    });
}

function renderizarChartHorasPerdidasSetor(dados) {
    const ctx = document.getElementById('chartHorasPerdidasSetor');
    if (!ctx || !dados || dados.length === 0) return;
    
    destruirGraficoSeguro('chartHorasPerdidasSetor', window.chartHorasPerdidasSetor);
    window.chartHorasPerdidasSetor = null;
    
    // Ordena por horas perdidas (decrescente) e pega top 10
    const dadosOrdenados = [...dados].sort((a, b) => (b.horas_perdidas || 0) - (a.horas_perdidas || 0));
    const top10 = dadosOrdenados.slice(0, 10);
    const paleta = getPaleta();
    
    window.chartHorasPerdidasSetor = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(d => truncate(d.setor, 20)),
            datasets: [{
                label: 'Horas Perdidas',
                data: top10.map(d => d.horas_perdidas),
                backgroundColor: paleta[0],
                borderColor: paleta[0],
                borderWidth: 1
            }, {
                label: 'Semanas Perdidas',
                data: top10.map(d => d.semanas_perdidas),
                backgroundColor: paleta[1],
                borderColor: paleta[1],
                borderWidth: 1,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'TOP 10 Setores - Horas Perdidas',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 20 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            if (label === 'Semanas Perdidas') {
                                return `${label}: ${value.toFixed(1)} semanas`;
                            }
                            return `${label}: ${value.toFixed(1)}h`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxRotation: 45, minRotation: 45 }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Horas' },
                    grid: { color: '#f0f0f0' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    beginAtZero: true,
                    title: { display: true, text: 'Semanas (44h)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

function renderizarChartEvolucaoMensalHoras(dados) {
    const ctx = document.getElementById('chartEvolucaoMensalHoras');
    if (!ctx || !dados || dados.length === 0) return;
    
    destruirGraficoSeguro('chartEvolucaoMensalHoras', window.chartEvolucaoMensalHoras);
    window.chartEvolucaoMensalHoras = null;
    
    const cores = getCores();
    
    window.chartEvolucaoMensalHoras = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dados.map(d => d.mes),
            datasets: [{
                label: 'Horas Perdidas',
                data: dados.map(d => d.horas_perdidas),
                borderColor: cores.primary,
                backgroundColor: cores.primary + '20',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }, {
                label: 'Semanas Perdidas (44h)',
                data: dados.map(d => d.semanas_perdidas),
                borderColor: cores.secondary,
                backgroundColor: cores.secondary + '20',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Evolução Mensal de Horas Perdidas',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 20 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            if (label.includes('Semanas')) {
                                return `${label}: ${value.toFixed(1)} semanas`;
                            }
                            return `${label}: ${value.toFixed(1)}h`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Horas' },
                    grid: { color: '#f0f0f0' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    beginAtZero: true,
                    title: { display: true, text: 'Semanas (44h)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

function renderizarChartComparativoDiasHorasGenero(dados) {
    const ctx = document.getElementById('chartComparativoDiasHorasGenero');
    if (!ctx || !dados || dados.length === 0) return;
    
    destruirGraficoSeguro('chartComparativoDiasHorasGenero', window.chartComparativoDiasHorasGenero);
    window.chartComparativoDiasHorasGenero = null;
    
    const cores = getCores();
    
    // Ordena: Masculino primeiro, depois ordena por dias perdidos (decrescente)
    const dadosOrdenados = [...dados].sort((a, b) => {
        // Primeiro: Masculino (M) vem antes de Feminino (F)
        if (a.genero === 'M' && b.genero !== 'M') return -1;
        if (a.genero !== 'M' && b.genero === 'M') return 1;
        // Se ambos são do mesmo gênero, ordena por dias perdidos (decrescente)
        return (b.dias_perdidos || 0) - (a.dias_perdidos || 0);
    });
    
    window.chartComparativoDiasHorasGenero = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dadosOrdenados.map(d => d.genero_label),
            datasets: [{
                label: 'Dias Perdidos',
                data: dadosOrdenados.map(d => d.dias_perdidos),
                backgroundColor: cores.primary,
                borderColor: cores.primaryDark,
                borderWidth: 1
            }, {
                label: 'Horas Perdidas',
                data: dadosOrdenados.map(d => d.horas_perdidas),
                backgroundColor: cores.secondary,
                borderColor: cores.secondaryDark,
                borderWidth: 1,
                yAxisID: 'y1'
            }, {
                label: 'Semanas Perdidas',
                data: dadosOrdenados.map(d => d.semanas_perdidas),
                backgroundColor: cores.primaryLight,
                borderColor: cores.primary,
                borderWidth: 1,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Comparativo: Dias vs Horas vs Semanas por Gênero',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 20 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            if (label.includes('Semanas')) {
                                return `${label}: ${value.toFixed(1)} semanas`;
                            } else if (label.includes('Horas')) {
                                return `${label}: ${value.toFixed(1)}h`;
                            }
                            return `${label}: ${value.toFixed(1)} dias`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Dias' },
                    grid: { color: '#f0f0f0' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    beginAtZero: true,
                    title: { display: true, text: 'Horas / Semanas' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

function renderizarChartHorasPerdidasSetorGenero(dados) {
    const ctx = document.getElementById('chartHorasPerdidasSetorGenero');
    if (!ctx || !dados || dados.length === 0) return;
    
    destruirGraficoSeguro('chartHorasPerdidasSetorGenero', window.chartHorasPerdidasSetorGenero);
    window.chartHorasPerdidasSetorGenero = null;
    
    // Agrupa por setor e calcula total de horas por setor
    const setoresUnicos = [...new Set(dados.map(d => d.setor))];
    const generos = ['M', 'F'];
    
    // Calcula total de horas por setor (soma M + F) para ordenação
    const setoresComTotal = setoresUnicos.map(setor => {
        const totalHoras = dados
            .filter(d => d.setor === setor)
            .reduce((sum, d) => sum + (d.horas_perdidas || 0), 0);
        return { setor, totalHoras };
    });
    
    // Ordena por total de horas (decrescente)
    setoresComTotal.sort((a, b) => (b.totalHoras || 0) - (a.totalHoras || 0));
    const setoresOrdenados = setoresComTotal.map(s => s.setor);
    
    // Cores: Preto para Masculino, Dourado para Feminino
    const corMasculino = '#000000'; // Preto
    const corFeminino = '#FFD700';  // Dourado
    
    const datasets = generos.map((genero, idx) => {
        const generoLabel = genero === 'M' ? 'Masculino' : 'Feminino';
        const cor = genero === 'M' ? corMasculino : corFeminino;
        
        return {
            label: generoLabel,
            data: setoresOrdenados.map(setor => {
                const item = dados.find(d => d.setor === setor && d.genero === genero);
                return item ? item.horas_perdidas : 0;
            }),
            backgroundColor: cor + '80', // 80 = 50% de opacidade
            borderColor: cor,
            borderWidth: 2
        };
    });
    
    window.chartHorasPerdidasSetorGenero = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: setoresOrdenados.map(s => truncate(s, 20)),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Horas Perdidas por Setor e Gênero',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 20 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            const dataIndex = context.dataIndex;
                            const setor = setoresOrdenados[dataIndex];
                            const genero = generos[context.datasetIndex];
                            const item = dados.find(d => d.setor === setor && d.genero === genero);
                            const semanas = item ? item.semanas_perdidas : 0;
                            return `${label}: ${value.toFixed(1)}h (${semanas.toFixed(1)} semanas)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxRotation: 45, minRotation: 45 }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Horas Perdidas' },
                    grid: { color: '#f0f0f0' }
                }
            }
        }
    });
}

function renderizarChartAnaliseDetalhadaGenero(dados) {
    const ctx = document.getElementById('chartAnaliseDetalhadaGenero');
    if (!ctx || !dados || !dados.generos || dados.generos.length === 0) return;
    
    destruirGraficoSeguro('chartAnaliseDetalhadaGenero', window.chartAnaliseDetalhadaGenero);
    window.chartAnaliseDetalhadaGenero = null;
    
    // Ordena: Masculino primeiro
    const generos = [...dados.generos].sort((a, b) => {
        // Masculino (M) vem antes de Feminino (F)
        if (a.genero === 'M' && b.genero !== 'M') return -1;
        if (a.genero !== 'M' && b.genero === 'M') return 1;
        return 0;
    });
    const cores = getCores();
    
    window.chartAnaliseDetalhadaGenero = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: generos.map(g => g.genero_label),
            datasets: [{
                label: 'Percentual de Dias',
                data: generos.map(g => g.percentual_dias),
                backgroundColor: cores.primary,
                borderColor: cores.primaryDark,
                borderWidth: 1,
                yAxisID: 'y'
            }, {
                label: 'Percentual de Horas',
                data: generos.map(g => g.percentual_horas),
                backgroundColor: cores.secondary,
                borderColor: cores.secondaryDark,
                borderWidth: 1,
                yAxisID: 'y'
            }, {
                label: 'Percentual de Registros',
                data: generos.map(g => g.percentual_registros),
                backgroundColor: cores.primaryLight,
                borderColor: cores.primary,
                borderWidth: 1,
                yAxisID: 'y'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Análise Detalhada por Gênero - Percentuais',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 20 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            return `${label}: ${value.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: 'Percentual (%)' },
                    grid: { color: '#f0f0f0' }
                }
            }
        }
    });
}

// ==================== UTILITÁRIOS ====================
function truncate(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
}

// ==================== FILTROS SALVOS ====================

let filtrosSalvosAbertos = false;

function toggleFiltrosSalvos() {
    const dropdown = document.getElementById('dropdownFiltrosSalvos');
    if (!dropdown) return;
    
    filtrosSalvosAbertos = !filtrosSalvosAbertos;
    dropdown.style.display = filtrosSalvosAbertos ? 'block' : 'none';
    
    if (filtrosSalvosAbertos) {
        carregarFiltrosSalvos();
    }
}

async function carregarFiltrosSalvos() {
    const clientId = getClientId();
    if (!clientId) {
        const lista = document.getElementById('listaFiltrosSalvos');
        if (lista) {
            lista.innerHTML = '<div style="padding: 20px; text-align: center; color: #6c757d;">Selecione um cliente primeiro</div>';
        }
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/filtros-salvos?client_id=${clientId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao carregar filtros salvos');
        }
        
        const filtros = await response.json();
        renderizarListaFiltrosSalvos(filtros);
    } catch (error) {
        console.error('Erro ao carregar filtros salvos:', error);
        const lista = document.getElementById('listaFiltrosSalvos');
        if (lista) {
            lista.innerHTML = '<div style="padding: 20px; text-align: center; color: #dc3545;">Erro ao carregar filtros</div>';
        }
    }
}

function renderizarListaFiltrosSalvos(filtros) {
    const lista = document.getElementById('listaFiltrosSalvos');
    if (!lista) return;
    
    if (!filtros || filtros.length === 0) {
        lista.innerHTML = '<div style="padding: 20px; text-align: center; color: #6c757d; font-size: 12px;">Nenhum filtro salvo</div>';
        return;
    }
    
    lista.innerHTML = filtros.map(filtro => {
        const descricao = [];
        if (filtro.mes_inicio || filtro.mes_fim) {
            descricao.push(`${filtro.mes_inicio || '...'} a ${filtro.mes_fim || '...'}`);
        }
        if (filtro.funcionarios && filtro.funcionarios.length > 0) {
            descricao.push(`${filtro.funcionarios.length} funcionário(s)`);
        }
        if (filtro.setores && filtro.setores.length > 0) {
            descricao.push(`${filtro.setores.length} setor(es)`);
        }
        
        return `
            <div style="padding: 10px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                <div style="flex: 1; min-width: 0;">
                    <div style="font-weight: 600; font-size: 13px; color: #212529; margin-bottom: 4px;">${filtro.nome}</div>
                    <div style="font-size: 11px; color: #6c757d;">${descricao.length > 0 ? descricao.join(' • ') : 'Sem filtros específicos'}</div>
                </div>
                <div style="display: flex; gap: 4px;">
                    <button onclick="aplicarFiltroSalvo(${filtro.id})" style="padding: 4px 8px; background: #1a237e; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;" title="Aplicar">
                        <i class="fas fa-check"></i>
                    </button>
                    <button onclick="deletarFiltroSalvo(${filtro.id})" style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;" title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

async function aplicarFiltroSalvo(filtroId) {
    const clientId = getClientId();
    if (!clientId) {
        alert('Selecione um cliente primeiro');
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/filtros-salvos/${filtroId}/aplicar`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao aplicar filtro');
        }
        
        const filtro = await response.json();
        
        // Aplica os valores do filtro nos campos
        const mesInicioInput = document.getElementById('mesInicio');
        const mesFimInput = document.getElementById('mesFim');
        
        if (mesInicioInput && filtro.mes_inicio) {
            mesInicioInput.value = filtro.mes_inicio;
        }
        if (mesFimInput && filtro.mes_fim) {
            mesFimInput.value = filtro.mes_fim;
        }
        
        // Aplica funcionários (checkboxes)
        if (filtro.funcionarios && filtro.funcionarios.length > 0) {
            const checkboxes = document.querySelectorAll('#checkboxesFuncionarios input[type="checkbox"]');
            checkboxes.forEach(cb => {
                cb.checked = filtro.funcionarios.includes(cb.value);
            });
            atualizarTextoSelecionados('funcionarios');
        }
        
        // Aplica setores (checkboxes)
        if (filtro.setores && filtro.setores.length > 0) {
            const checkboxes = document.querySelectorAll('#checkboxesSetores input[type="checkbox"]');
            checkboxes.forEach(cb => {
                cb.checked = filtro.setores.includes(cb.value);
            });
            atualizarTextoSelecionados('setores');
        }
        
        // Fecha o dropdown
        toggleFiltrosSalvos();
        
        // Aplica os filtros automaticamente
        await aplicarFiltros();
        
        // Mostra mensagem de sucesso
        mostrarMensagemSucesso('Filtro aplicado com sucesso!');
    } catch (error) {
        console.error('Erro ao aplicar filtro:', error);
        alert('Erro ao aplicar filtro salvo');
    }
}

async function deletarFiltroSalvo(filtroId) {
    if (!confirm('Deseja realmente excluir este filtro salvo?')) {
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/filtros-salvos/${filtroId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao deletar filtro');
        }
        
        // Recarrega a lista
        await carregarFiltrosSalvos();
        mostrarMensagemSucesso('Filtro excluído com sucesso!');
    } catch (error) {
        console.error('Erro ao deletar filtro:', error);
        alert('Erro ao excluir filtro salvo');
    }
}

async function salvarFiltroAtual() {
    const clientId = getClientId();
    if (!clientId) {
        alert('Selecione um cliente primeiro');
        return;
    }
    
    const nome = prompt('Digite um nome para este filtro:');
    if (!nome || nome.trim() === '') {
        return;
    }
    
    // Coleta valores atuais dos filtros
    const mesInicio = document.getElementById('mesInicio')?.value || '';
    const mesFim = document.getElementById('mesFim')?.value || '';
    
    // Pega funcionários selecionados
    const funcionarios = Array.from(document.querySelectorAll('#checkboxesFuncionarios input[type="checkbox"]:checked'))
        .map(cb => cb.value)
        .filter(v => v);
    
    // Pega setores selecionados
    const setores = Array.from(document.querySelectorAll('#checkboxesSetores input[type="checkbox"]:checked'))
        .map(cb => cb.value)
        .filter(v => v);
    
    try {
        const token = localStorage.getItem('access_token');
        const formData = new FormData();
        formData.append('client_id', clientId);
        formData.append('nome', nome.trim());
        if (mesInicio) formData.append('mes_inicio', mesInicio);
        if (mesFim) formData.append('mes_fim', mesFim);
        if (funcionarios.length > 0) formData.append('funcionarios', JSON.stringify(funcionarios));
        if (setores.length > 0) formData.append('setores', JSON.stringify(setores));
        
        const response = await fetch('/api/filtros-salvos', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao salvar filtro');
        }
        
        mostrarMensagemSucesso('Filtro salvo com sucesso!');
        
        // Recarrega a lista se o dropdown estiver aberto
        if (filtrosSalvosAbertos) {
            await carregarFiltrosSalvos();
        }
    } catch (error) {
        console.error('Erro ao salvar filtro:', error);
        alert(error.message || 'Erro ao salvar filtro');
    }
}

function mostrarMensagemSucesso(mensagem) {
    // Cria ou atualiza mensagem de sucesso
    let msgDiv = document.getElementById('mensagemSucessoFiltros');
    if (!msgDiv) {
        msgDiv = document.createElement('div');
        msgDiv.id = 'mensagemSucessoFiltros';
        msgDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; padding: 12px 20px; background: #28a745; color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 10000; font-size: 13px;';
        document.body.appendChild(msgDiv);
    }
    
    msgDiv.textContent = mensagem;
    msgDiv.style.display = 'block';
    
    setTimeout(() => {
        msgDiv.style.display = 'none';
    }, 3000);
}

// ==================== COMPARATIVO ENTRE PERÍODOS ====================

let chartComparativoMensal = null;
let chartComparativoTrimestral = null;

function renderizarChartComparativoMensal(dados) {
    const ctx = document.getElementById('chartComparativoMensal');
    if (!ctx || !dados || !dados.periodo_atual) return;
    
    destruirGraficoSeguro('chartComparativoMensal', chartComparativoMensal);
    chartComparativoMensal = null;
    
    const cores = getCores();
    const periodoAtual = dados.periodo_atual;
    const periodoAnterior = dados.periodo_anterior;
    const variacao = dados.variacao;
    
    chartComparativoMensal = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Dias Perdidos', 'Horas Perdidas', 'Total de Registros'],
            datasets: [
                {
                    label: periodoAtual.label || 'Período Atual',
                    data: [
                        periodoAtual.dias_perdidos || 0,
                        periodoAtual.horas_perdidas || 0,
                        periodoAtual.total_registros || 0
                    ],
                    backgroundColor: cores.primary,
                    borderRadius: 6
                },
                {
                    label: periodoAnterior.label || 'Período Anterior',
                    data: [
                        periodoAnterior.dias_perdidos || 0,
                        periodoAnterior.horas_perdidas || 0,
                        periodoAnterior.total_registros || 0
                    ],
                    backgroundColor: cores.secondary,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { font: { size: 12 } }
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const index = context.dataIndex;
                            const datasetIndex = context.datasetIndex;
                            let variacaoValor = 0;
                            
                            if (index === 0) variacaoValor = variacao.dias_perdidos;
                            else if (index === 1) variacaoValor = variacao.horas_perdidas;
                            else if (index === 2) variacaoValor = variacao.total_registros;
                            
                            if (datasetIndex === 0 && variacaoValor !== 0) {
                                const sinal = variacaoValor > 0 ? '+' : '';
                                const cor = variacaoValor > 0 ? '🔴' : '🟢';
                                return `${cor} Variação: ${sinal}${variacaoValor.toFixed(1)}%`;
                            }
                            return '';
                        }
                    }
                },
                title: {
                    display: true,
                    text: `Comparativo: ${periodoAtual.label} vs ${periodoAnterior.label}`,
                    font: { size: 14, weight: 'bold' },
                    padding: { bottom: 10 }
                }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderizarChartComparativoTrimestral(dados) {
    const ctx = document.getElementById('chartComparativoTrimestral');
    if (!ctx || !dados || !dados.periodo_atual) return;
    
    destruirGraficoSeguro('chartComparativoTrimestral', chartComparativoTrimestral);
    chartComparativoTrimestral = null;
    
    const cores = getCores();
    const periodoAtual = dados.periodo_atual;
    const periodoAnterior = dados.periodo_anterior;
    const variacao = dados.variacao;
    
    chartComparativoTrimestral = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Dias Perdidos', 'Horas Perdidas', 'Total de Registros'],
            datasets: [
                {
                    label: periodoAtual.label || 'Trimestre Atual',
                    data: [
                        periodoAtual.dias_perdidos || 0,
                        periodoAtual.horas_perdidas || 0,
                        periodoAtual.total_registros || 0
                    ],
                    backgroundColor: cores.primary,
                    borderRadius: 6
                },
                {
                    label: periodoAnterior.label || 'Trimestre Anterior',
                    data: [
                        periodoAnterior.dias_perdidos || 0,
                        periodoAnterior.horas_perdidas || 0,
                        periodoAnterior.total_registros || 0
                    ],
                    backgroundColor: cores.secondary,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { font: { size: 12 } }
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const index = context.dataIndex;
                            const datasetIndex = context.datasetIndex;
                            let variacaoValor = 0;
                            
                            if (index === 0) variacaoValor = variacao.dias_perdidos;
                            else if (index === 1) variacaoValor = variacao.horas_perdidas;
                            else if (index === 2) variacaoValor = variacao.total_registros;
                            
                            if (datasetIndex === 0 && variacaoValor !== 0) {
                                const sinal = variacaoValor > 0 ? '+' : '';
                                const cor = variacaoValor > 0 ? '🔴' : '🟢';
                                return `${cor} Variação: ${sinal}${variacaoValor.toFixed(1)}%`;
                            }
                            return '';
                        }
                    }
                },
                title: {
                    display: true,
                    text: `Comparativo Trimestral`,
                    font: { size: 14, weight: 'bold' },
                    padding: { bottom: 10 }
                }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Torna funções globais
window.toggleFiltrosSalvos = toggleFiltrosSalvos;
window.salvarFiltroAtual = salvarFiltroAtual;
window.aplicarFiltroSalvo = aplicarFiltroSalvo;
window.deletarFiltroSalvo = deletarFiltroSalvo;

