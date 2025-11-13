const DEFAULT_BRANDING = {
    primary: '#1a237e',
    primaryDark: '#0d47a1',
    primaryLight: '#3949ab',
    secondary: '#556B2F',
    secondaryLight: '#6B8E23',
    background: '#F5F7FA',
    gradient: 'linear-gradient(135deg, #1a237e, #3949ab)',
    logoText: 'AC'
};

const CLIENTE_BRANDING = [
    {
        keywords: ['grupobiomed', 'biomed'],
        branding: {
            primary: '#1a237e',
            primaryDark: '#121858',
            primaryLight: '#3949ab',
            secondary: '#6B8E23',
            secondaryLight: '#A5D6A7',
            background: '#f4f7fb',
            gradient: 'linear-gradient(135deg, #1a237e, #3949ab)',
            logoText: 'GB'
        }
    },
    {
        keywords: ['converplast', 'conver'],
        branding: {
            primary: '#004aad',
            primaryDark: '#00337a',
            primaryLight: '#1976d2',
            secondary: '#ff9800',
            secondaryLight: '#ffb74d',
            background: '#f3f7ff',
            gradient: 'linear-gradient(135deg, #004aad, #1976d2)',
            logoText: 'CV'
        }
    }
];

let clientes = [];
let clienteEditando = null;
let filtroStatus = 'todos';
let logoArquivoSelecionado = null;
let logoPreviewTempUrl = null;
let logoRemoverSelecionado = false;
let logoPreviewElemento = null;

document.addEventListener('DOMContentLoaded', () => {
    registrarFiltros();
    carregarClientes();
    configurarLogoUpload();
    
    const modal = document.getElementById('modalCliente');
    if (modal) {
        modal.addEventListener('click', (e) => {
        if (e.target.id === 'modalCliente') {
            fecharModal();
        }
    });
    }
});

// ==================== CLIENTE & SELEÇÃO ====================
function getCurrentClientIdLocal(fallback = 0) {
    if (typeof getCurrentClientId === 'function') {
        return getCurrentClientId(fallback);
    }
    const stored = Number(localStorage.getItem('cliente_selecionado'));
    return Number.isFinite(stored) && stored > 0 ? stored : fallback;
}

function obterBrandingCliente(cliente) {
    const nomeComparacao = (cliente?.nome_fantasia || cliente?.nome || '').toLowerCase();
    for (const entry of CLIENTE_BRANDING) {
        if (entry.keywords.some(keyword => nomeComparacao.includes(keyword))) {
            return { ...DEFAULT_BRANDING, ...entry.branding };
        }
    }
    return { ...DEFAULT_BRANDING };
}

function limparCacheGraficos() {
    /**
     * Limpa todos os gráficos e cache ao trocar de cliente
     * Isso evita que dados de um cliente apareçam em outro
     */
    console.log('[CACHE] Limpando gráficos e cache...');
    
    // Destrói todos os gráficos Chart.js globais
    if (window.chartCids && typeof window.chartCids.destroy === 'function') {
        window.chartCids.destroy();
        window.chartCids = null;
    }
    if (window.chartSetores && typeof window.chartSetores.destroy === 'function') {
        window.chartSetores.destroy();
        window.chartSetores = null;
    }
    if (window.chartEvolucao && typeof window.chartEvolucao.destroy === 'function') {
        window.chartEvolucao.destroy();
        window.chartEvolucao = null;
    }
    if (window.chartGenero && typeof window.chartGenero.destroy === 'function') {
        window.chartGenero.destroy();
        window.chartGenero = null;
    }
    if (window.chartProdutividade && typeof window.chartProdutividade.destroy === 'function') {
        window.chartProdutividade.destroy();
        window.chartProdutividade = null;
    }
    if (window.chartProdutividadeEvolucao && typeof window.chartProdutividadeEvolucao.destroy === 'function') {
        window.chartProdutividadeEvolucao.destroy();
        window.chartProdutividadeEvolucao = null;
    }
    // Limpa outros gráficos conhecidos
    Object.keys(window).forEach(key => {
        if (key.startsWith('chart') && window[key] && typeof window[key].destroy === 'function') {
            try {
                window[key].destroy();
                window[key] = null;
            } catch (e) {
                console.warn(`[CACHE] Erro ao destruir gráfico ${key}:`, e);
            }
        }
    });
    
    // Limpa dados em cache
    if (window.camposDisponiveis) {
        window.camposDisponiveis = {};
    }
    if (window.alertasData) {
        window.alertasData = [];
    }
    
    // Força recarregamento da página se estiver no dashboard
    if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
        console.log('[CACHE] Recarregando dashboard...');
        setTimeout(() => {
            if (typeof carregarDashboard === 'function') {
                carregarDashboard();
            } else {
                window.location.reload();
            }
        }, 100);
    }
    
    console.log('[CACHE] Cache limpo com sucesso');
}

function salvarSelecaoCliente(cliente, branding) {
    // Limpa cache antes de trocar
    limparCacheGraficos();
    
    localStorage.setItem('cliente_selecionado', cliente.id);
    localStorage.setItem('cliente_nome', cliente.nome_fantasia || cliente.nome || '');
    if (cliente.cnpj) {
        localStorage.setItem('cliente_cnpj', cliente.cnpj);
    }
    if (cliente.logo_url) {
        localStorage.setItem('cliente_logo_url', cliente.logo_url);
    } else {
        localStorage.removeItem('cliente_logo_url');
    }

    const tema = {
        primary: branding.primary,
        primaryDark: branding.primaryDark || branding.primary,
        primaryLight: branding.primaryLight || branding.primary,
        secondary: branding.secondary || DEFAULT_BRANDING.secondary,
        secondaryLight: branding.secondaryLight || DEFAULT_BRANDING.secondaryLight,
        background: branding.background || DEFAULT_BRANDING.background
    };
    localStorage.setItem('cliente_tema', JSON.stringify(tema));
    
    console.log(`[CLIENTE] Cliente alterado para: ${cliente.nome} (ID: ${cliente.id})`);
}

function atualizarSelecaoVisual(selectedId) {
    document.querySelectorAll('.cliente-card').forEach(card => {
        const id = Number(card.dataset.clienteId);
        card.classList.toggle('selected', id === selectedId);
    });
    document.querySelectorAll('.clientes-table tbody tr').forEach(row => {
        const id = Number(row.dataset.clienteId);
        row.classList.toggle('selected-row', id === selectedId);
    });
}

function refreshClientesUI(selectedId) {
    renderizarSnapshot();
    renderizarHighlights();
    renderizarCards();
    atualizarFiltroUI();
    if (selectedId) {
        atualizarSelecaoVisual(selectedId);
    }
    carregarAlertasHome();
}

// ==================== CARREGAMENTO ====================
async function carregarClientes() {
    try {
        const response = await fetch('/api/clientes');
        if (!response.ok) throw new Error('Erro ao carregar clientes');
        
        clientes = await response.json();
        refreshClientesUI(getCurrentClientIdLocal(0));
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
        mostrarErro('Erro ao carregar clientes: ' + error.message);
    }
}

// ==================== LOGO ====================
function configurarLogoUpload() {
    logoPreviewElemento = document.getElementById('logoPreview');

    const inputArquivo = document.getElementById('logoArquivo');
    if (inputArquivo) {
        inputArquivo.addEventListener('change', (event) => {
            const arquivo = event.target.files && event.target.files[0] ? event.target.files[0] : null;
            if (!arquivo) {
                return;
            }

            if (!arquivo.type || !arquivo.type.startsWith('image/')) {
                mostrarErro('Selecione um arquivo de imagem (PNG, JPG, SVG ou WEBP).');
                event.target.value = '';
                return;
            }

            if (arquivo.size > 1024 * 1024) {
                mostrarErro('Logo deve ter no máximo 1 MB.');
                event.target.value = '';
                return;
            }

            if (logoPreviewTempUrl) {
                URL.revokeObjectURL(logoPreviewTempUrl);
                logoPreviewTempUrl = null;
            }

            logoArquivoSelecionado = arquivo;
            logoRemoverSelecionado = false;
            const objectUrl = URL.createObjectURL(arquivo);
            logoPreviewTempUrl = objectUrl;
            atualizarPreviewLogo(objectUrl, false);
        });
    }

    const nomeInput = document.getElementById('nome');
    const fantasiaInput = document.getElementById('nome_fantasia');
    const atualizar = () => atualizarIniciaisLogoSeNecessario();
    if (nomeInput) nomeInput.addEventListener('input', atualizar);
    if (fantasiaInput) fantasiaInput.addEventListener('input', atualizar);
}

function atualizarPreviewLogo(logoSrc = '', usarIniciais = false, textoIniciais = '') {
    if (!logoPreviewElemento) {
        logoPreviewElemento = document.getElementById('logoPreview');
    }
    if (!logoPreviewElemento) return;

    logoPreviewElemento.innerHTML = '';

    if (logoSrc) {
        const img = document.createElement('img');
        img.src = logoSrc;
        img.alt = 'Logo do cliente';
        logoPreviewElemento.appendChild(img);
        return;
    }

    if (usarIniciais && textoIniciais) {
        const span = document.createElement('span');
        span.className = 'logo-preview-initials';
        span.textContent = textoIniciais.slice(0, 2).toUpperCase();
        logoPreviewElemento.appendChild(span);
        return;
    }

    const vazio = document.createElement('div');
    vazio.className = 'logo-preview-empty';
    vazio.innerHTML = '<i class="fas fa-image"></i><span>Sem logo</span>';
    logoPreviewElemento.appendChild(vazio);
}

function resetLogoPreview(logoUrl = '', iniciais = '') {
    if (logoPreviewTempUrl) {
        URL.revokeObjectURL(logoPreviewTempUrl);
        logoPreviewTempUrl = null;
    }
    logoArquivoSelecionado = null;
    logoRemoverSelecionado = false;

    const inputArquivo = document.getElementById('logoArquivo');
    if (inputArquivo) {
        inputArquivo.value = '';
    }

    const logoUrlInput = document.getElementById('logoUrl');
    if (logoUrlInput) {
        logoUrlInput.value = logoUrl || '';
    }

    if (logoUrl) {
        atualizarPreviewLogo(logoUrl, false);
    } else {
        atualizarPreviewLogo('', Boolean(iniciais), iniciais);
    }
}

function removerLogoSelecionado() {
    const logoUrlInput = document.getElementById('logoUrl');
    const possuiLogoExistente = Boolean(logoUrlInput && logoUrlInput.value);

    if (logoPreviewTempUrl) {
        URL.revokeObjectURL(logoPreviewTempUrl);
        logoPreviewTempUrl = null;
    }

    logoArquivoSelecionado = null;

    const inputArquivo = document.getElementById('logoArquivo');
    if (inputArquivo) {
        inputArquivo.value = '';
    }

    if (logoUrlInput) {
        if (possuiLogoExistente) {
            logoRemoverSelecionado = true;
        } else {
            logoRemoverSelecionado = false;
        }
        logoUrlInput.value = '';
    } else {
        logoRemoverSelecionado = false;
    }

    atualizarIniciaisLogoSeNecessario(true);
}

function atualizarIniciaisLogoSeNecessario(force = false) {
    if (!logoPreviewElemento) {
        logoPreviewElemento = document.getElementById('logoPreview');
    }
    if (!logoPreviewElemento) return;

    const temArquivoSelecionado = Boolean(logoArquivoSelecionado);
    const logoAtual = document.getElementById('logoUrl')?.value || '';

    if (!force) {
        if (temArquivoSelecionado) return;
        if (logoAtual && !logoRemoverSelecionado) return;
    }

    const nomeFantasia = document.getElementById('nome_fantasia')?.value || '';
    const nomeRazao = document.getElementById('nome')?.value || '';
    const base = nomeFantasia || nomeRazao || 'Cliente';
    const iniciais = gerarIniciais(base);
    atualizarPreviewLogo('', true, iniciais);
}

async function enviarLogoCliente(clienteId) {
    if (!logoArquivoSelecionado) return null;

    const formData = new FormData();
    formData.append('arquivo', logoArquivoSelecionado);

    const response = await fetch(`/api/clientes/${clienteId}/logo`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Erro ao enviar logo');
    }

    const data = await response.json();
    const logoUrl = data.logo_url || '';
    const logoUrlInput = document.getElementById('logoUrl');
    if (logoUrlInput) {
        logoUrlInput.value = logoUrl;
    }

    if (logoPreviewTempUrl) {
        URL.revokeObjectURL(logoPreviewTempUrl);
        logoPreviewTempUrl = null;
    }
    logoArquivoSelecionado = null;
    atualizarPreviewLogo(logoUrl, false);

    return logoUrl;
}
// ==================== RENDERIZAÇÃO DE CARDS ====================
function renderizarCards() {
    const container = document.getElementById('clientesCards');
    if (!container) return;

    if (!clientes || clientes.length === 0) {
        container.innerHTML = `
            <div class="clientes-empty">
                <i class="fas fa-building"></i>
                <h3>Nenhum cliente cadastrado</h3>
                <p>Clique em "Adicionar Novo Cliente" para começar.</p>
            </div>
        `;
        return;
    }

    const clienteSelecionado = getCurrentClientIdLocal(0);
    const filtrados = clientes.filter(cliente => correspondeFiltroStatus(cliente, filtroStatus));

    if (filtrados.length === 0) {
        container.innerHTML = `
            <div class="clientes-empty">
                <i class="fas fa-filter"></i>
                <h3>Nenhum cliente neste filtro</h3>
                <p>Tente selecionar outra opção para visualizar os clientes.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtrados.map(cliente => {
        const branding = obterBrandingCliente(cliente);
        const nomeFantasia = cliente.nome_fantasia || cliente.nome;
        const initials = branding.logoText || gerarIniciais(nomeFantasia || '');
        const totalUploads = cliente.total_uploads || 0;
        const cidade = cliente.cidade ? `${cliente.cidade}${cliente.estado ? '/' + cliente.estado : ''}` : '-';
        const situacao = (cliente.situacao || 'Ativa').toUpperCase();
        const atualizadoEm = formatarDataCurta(cliente.updated_at || cliente.created_at);
        const cadastradoEm = formatarDataCurta(cliente.created_at);
        const contato = cliente.telefone || cliente.email || '-';
        const temDados = totalUploads > 0;
        const arquivado = situacao === 'ARQUIVO MORTO';
        const statusLabel = arquivado ? 'Arquivo morto' : (temDados ? 'Ativo' : 'Sem dados');
        const statusIcon = arquivado ? 'fa-archive' : (temDados ? 'fa-check-circle' : 'fa-database');
        const statusClass = arquivado ? 'status-archive' : (temDados ? 'status-active' : 'status-empty');
        const actionClass = arquivado ? 'btn-reactivate' : (temDados ? 'btn-archive' : 'btn-delete');
        const actionIcon = arquivado ? 'fa-recycle' : (temDados ? 'fa-archive' : 'fa-trash');
        const actionLabel = arquivado ? 'Ativar' : (temDados ? 'Arquivar' : 'Excluir');
        const selectedClass = clienteSelecionado === cliente.id ? 'selected' : '';
        const logoUrl = (cliente.logo_url || '').trim();
        const temLogo = logoUrl.length > 0;
        const logoMarkup = temLogo
            ? `<img src="${logoUrl}" alt="Logo ${nomeFantasia || cliente.nome || ''}" onerror="this.remove(); this.parentElement.classList.remove('has-image'); this.parentElement.innerHTML='<span>${initials}</span>';">`
            : `<span>${initials}</span>`;

        return `
            <article class="cliente-card ${selectedClass}" data-cliente-id="${cliente.id}" style="--cliente-cor:${branding.primary}; --cliente-banner:${branding.gradient}; --cliente-sec:${branding.secondary};">
                <div class="cliente-card-header">
                    <div class="cliente-card-identidade">
                        <div class="cliente-card-logo ${temLogo ? 'has-image' : ''}">
                            ${logoMarkup}
                        </div>
                        <div class="cliente-card-titulos">
                            <h3 title="${nomeFantasia || 'Cliente sem nome'}">${nomeFantasia || 'Cliente sem nome'}</h3>
                            <span>${formatarCNPJExibicao(cliente.cnpj) || cliente.nome || '-'}</span>
                        </div>
                    </div>
                    <div class="cliente-card-highlights">
                        <div class="cliente-card-highlight">
                            <span class="label">Uploads</span>
                            <span class="value"><i class="fas fa-upload"></i>${totalUploads}</span>
                        </div>
                        <div class="cliente-card-highlight">
                            <span class="label">Atualização</span>
                            <span class="value"><i class="fas fa-clock"></i>${atualizadoEm}</span>
                        </div>
                    </div>
                </div>
                <div class="cliente-card-body">
                    <div class="cliente-status-chip ${statusClass}">
                        <i class="fas ${statusIcon}"></i>
                        ${statusLabel}
                    </div>
                    <div class="cliente-meta-grid">
                        <div class="cliente-meta-item situacao-item" data-situacao="${situacao.toLowerCase().replace(' ', '-')}">
                            <span>Situação</span>
                            <strong>${situacao}</strong>
                        </div>
                        <div class="cliente-meta-item">
                            <span>Cadastro</span>
                            <strong>${cadastradoEm}</strong>
                        </div>
                        <div class="cliente-meta-item">
                            <span>Local</span>
                            <strong>${cidade}</strong>
                        </div>
                        <div class="cliente-meta-item">
                            <span>Contato</span>
                            <strong>${contato}</strong>
                        </div>
                    </div>
                </div>
                <div class="cliente-card-actions">
                    <div class="cliente-card-actions-left">
                        <button type="button" class="btn-card btn-card-secondary" onclick="event.stopPropagation(); editarCliente(${cliente.id})" title="Editar">
                            <i class="fas fa-pen"></i>
                        </button>
                        <button type="button" class="btn-card btn-card-info" onclick="event.stopPropagation(); configurarMapeamento(${cliente.id})" title="Configurar Mapeamento de Planilha">
                            <i class="fas fa-table-columns"></i>
                        </button>
                        <button type="button" class="btn-card ${actionClass}" onclick="event.stopPropagation(); confirmarDeletar(${cliente.id})" title="${actionLabel}">
                            <i class="fas ${actionIcon}"></i>
                        </button>
                    </div>
                    <button type="button" class="btn-card btn-card-enter" onclick="entrarCliente(event, ${cliente.id})">
                        <i class="fas fa-sign-in-alt"></i> Entrar
                    </button>
                </div>
            </article>
        `;
    }).join('');

    container.querySelectorAll('.cliente-card').forEach(card => {
        card.addEventListener('click', (event) => {
            if (event.target.closest('.btn-card')) return;
            entrarCliente(event, Number(card.dataset.clienteId));
        });
    });
}

function correspondeFiltroStatus(cliente, status) {
    if (!cliente) return false;
    const situacao = (cliente.situacao || '').toUpperCase();
    const temDados = (cliente.total_uploads || 0) > 0;

    switch (status) {
        case 'ativos':
            return situacao !== 'ARQUIVO MORTO' && temDados;
        case 'arquivo':
            return situacao === 'ARQUIVO MORTO';
        case 'sem-dados':
            return !temDados;
        default:
            return true;
    }
}

function registrarFiltros() {
    const filtrosContainer = document.getElementById('clientesFilters');
    if (!filtrosContainer) return;

    filtrosContainer.addEventListener('click', (event) => {
        const button = event.target.closest('.filter-chip');
        if (!button) return;
        const status = button.dataset.status;
        if (!status || status === filtroStatus) return;
        filtroStatus = status;
        atualizarFiltroUI();
        renderizarCards();
    });

    atualizarFiltroUI();
}

function atualizarFiltroUI() {
    const filtrosContainer = document.getElementById('clientesFilters');
    if (!filtrosContainer) return;

    filtrosContainer.querySelectorAll('.filter-chip').forEach(button => {
        button.classList.toggle('active', button.dataset.status === filtroStatus);
    });
}

function formatarNumero(valor) {
    const numero = Number(valor || 0);
    return numero.toLocaleString('pt-BR');
}

function renderizarSnapshot() {
    const container = document.getElementById('clientesSnapshot');
    if (!container) return;

    if (!clientes || clientes.length === 0) {
        container.innerHTML = `
            <div class="snapshot-card">
                <span class="label"><i class="fas fa-building"></i> Clientes</span>
                <div class="value">0</div>
                <span class="detail">Nenhuma empresa cadastrada ainda</span>
            </div>
        `;
        return;
    }

    const totalClientes = clientes.length;
    const ativos = clientes.filter(c => correspondeFiltroStatus(c, 'ativos')).length;
    const arquivados = clientes.filter(c => correspondeFiltroStatus(c, 'arquivo')).length;
    const semDados = clientes.filter(c => correspondeFiltroStatus(c, 'sem-dados')).length;
    const totalUploads = clientes.reduce((acc, c) => acc + (c.total_uploads || 0), 0);

    let ultimaAtualizacao = null;
    clientes.forEach(cliente => {
        const dataStr = cliente.updated_at || cliente.created_at;
        if (!dataStr) return;
        const data = new Date(dataStr);
        if (Number.isNaN(data.getTime())) return;
        if (!ultimaAtualizacao || data > ultimaAtualizacao.data) {
            ultimaAtualizacao = {
                data,
                dataStr,
                cliente
            };
        }
    });

    const ultimaData = ultimaAtualizacao ? formatarDataCurta(ultimaAtualizacao.dataStr) : '-';
    const ultimaCliente = ultimaAtualizacao ? (ultimaAtualizacao.cliente.nome_fantasia || ultimaAtualizacao.cliente.nome || 'Cliente') : 'Sem registros';
    
    container.innerHTML = `
        <div class="snapshot-card">
            <span class="label"><i class="fas fa-layer-group"></i> Clientes</span>
            <div class="value">${formatarNumero(totalClientes)}</div>
            <span class="detail">Empresas cadastradas</span>
        </div>
        <div class="snapshot-card">
            <span class="label"><i class="fas fa-check-circle"></i> Ativos</span>
            <div class="value">${formatarNumero(ativos)}</div>
            <span class="detail">${ativos === 1 ? 'Empresa com dados ativos' : 'Empresas com dados ativos'}</span>
        </div>
        <div class="snapshot-card">
            <span class="label"><i class="fas fa-archive"></i> Arquivo morto</span>
            <div class="value">${formatarNumero(arquivados)}</div>
            <span class="detail">${arquivados === 1 ? 'Empresa arquivada' : 'Empresas arquivadas'}</span>
        </div>
        <div class="snapshot-card">
            <span class="label"><i class="fas fa-database"></i> Sem dados</span>
            <div class="value">${formatarNumero(semDados)}</div>
            <span class="detail">${semDados === 1 ? 'Empresa aguardando uploads' : 'Empresas aguardando uploads'}</span>
        </div>
    `;
}

function renderizarHighlights() {
    const container = document.getElementById('clientesHighlights');
    if (!container) return;

    if (!clientes || clientes.length === 0) {
        container.innerHTML = `
            <h3><i class="fas fa-star"></i> Novidades</h3>
            <div class="clientes-empty-sm">
                <i class="fas fa-info-circle"></i>
                <p>Cadastre empresas para ver novidades e recomendações.</p>
            </div>
        `;
        return;
    }

    const ativos = clientes.filter(c => correspondeFiltroStatus(c, 'ativos')).length;
    const arquivados = clientes.filter(c => correspondeFiltroStatus(c, 'arquivo')).length;
    const uploads = clientes.reduce((acc, c) => acc + (c.total_uploads || 0), 0);

    container.innerHTML = `
        <h3><i class="fas fa-star"></i> Novidades</h3>
        <ul class="highlights-list">
            <li>
                <span class="highlight-title">${formatarNumero(ativos)} clientes em operação</span>
                <span class="highlight-desc">Continue acompanhando os indicadores com insights automáticos em cada relatório.</span>
            </li>
            <li>
                <span class="highlight-title">${formatarNumero(uploads)} uploads processados</span>
                <span class="highlight-desc">Exportações em PDF, Excel e PowerPoint usam sempre os dados mais atualizados.</span>
            </li>
            <li>
                <span class="highlight-title">${formatarNumero(arquivados)} empresas arquivadas</span>
                <span class="highlight-desc">Reative quando quiser: os dados permanecem preservados no arquivo morto.</span>
            </li>
        </ul>
    `;
}

async function carregarAlertasHome() {
    const container = document.getElementById('clientesAlertas');
    if (!container) return;

    const clientId = getCurrentClientIdLocal(0);

    const header = `<h3><i class="fas fa-bell"></i> Alertas recentes</h3>`;

    if (!clientId) {
        container.innerHTML = `
            ${header}
            <div class="clientes-empty-sm">
                <i class="fas fa-info-circle"></i>
                <p>Selecione um cliente para visualizar os alertas automáticos.</p>
            </div>
        `;
        return;
    }

    try {
        const response = await fetch(`/api/alertas?client_id=${clientId}`);
        if (!response.ok) {
            throw new Error('Erro ao buscar alertas');
        }

        const data = await response.json();
        const alertas = Array.isArray(data) ? data : (data.alertas || []);

        if (!alertas.length) {
            container.innerHTML = `
                ${header}
                <div class="clientes-empty-sm">
                    <i class="fas fa-check-circle"></i>
                    <p>Nenhum alerta crítico no momento para este cliente.</p>
                </div>
                <div class="alert-actions">
                    <button type="button" class="btn-card btn-card-primary" onclick="entrarCliente(null, ${clientId})">
                        <i class="fas fa-sign-in-alt"></i> Entrar no cliente
                    </button>
                </div>
            `;
            return;
        }

        const itens = alertas.slice(0, 4).map(alerta => {
            const severidade = (alerta.severidade || alerta.nivel || 'info').toLowerCase();
            const classe = obterClasseSeveridadeAlerta(severidade);
            const icone = obterIconeSeveridadeAlerta(severidade);
            const titulo = alerta.titulo || alerta.tipo || 'Alerta automático';
            const mensagem = alerta.mensagem || alerta.descricao || 'Sem detalhes adicionais';

            return `
                <li class="alert-item ${classe}">
                    <div class="alert-icon"><i class="fas ${icone}"></i></div>
                    <div class="alert-content">
                        <span class="alert-title">${titulo}</span>
                        <span class="alert-message">${mensagem}</span>
                    </div>
                </li>
            `;
        }).join('');

        container.innerHTML = `
            ${header}
            <ul class="alert-list">
                ${itens}
            </ul>
            <div class="alert-actions">
                <button type="button" class="btn-card btn-card-primary" onclick="entrarCliente(null, ${clientId})">
                    <i class="fas fa-sign-in-alt"></i> Entrar no cliente
                </button>
            </div>
        `;
    } catch (error) {
        console.error('Erro ao carregar alertas:', error);
        container.innerHTML = `
            ${header}
            <div class="clientes-empty-sm">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Não foi possível carregar os alertas. Tente novamente mais tarde.</p>
            </div>
        `;
    }
}

function obterClasseSeveridadeAlerta(severidade) {
    switch (severidade) {
        case 'critico':
        case 'crítico':
        case 'alta':
            return 'severity-alta';
        case 'moderado':
        case 'media':
        case 'média':
            return 'severity-media';
        case 'baixa':
        case 'informativo':
        default:
            return 'severity-baixa';
    }
}

function obterIconeSeveridadeAlerta(severidade) {
    switch (severidade) {
        case 'critico':
        case 'crítico':
        case 'alta':
            return 'fa-exclamation-circle';
        case 'moderado':
        case 'media':
        case 'média':
            return 'fa-exclamation-triangle';
        default:
            return 'fa-info-circle';
    }
}

// ==================== RENDERIZAÇÃO DA TABELA ====================
function renderizarTabela() {
    // listagem detalhada removida da página inicial
}

// ==================== REPLICAÇÃO E ENTRADA ====================
async function replicarDadosCliente(cliente, triggerButton) {
    if (!cliente || cliente.total_uploads > 0) {
        return;
    }

    const confirmar = confirm(`Ainda não existem dados para ${cliente.nome_fantasia || cliente.nome}. Deseja replicar os dados do GrupoBioMed?`);
    if (!confirmar) {
        throw new Error('cancelado');
    }

    let originalHTML = null;
    if (triggerButton instanceof HTMLElement) {
        originalHTML = triggerButton.innerHTML;
        triggerButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Replicando...';
        triggerButton.disabled = true;
    }

    try {
        const response = await fetch(`/api/clientes/${cliente.id}/clonar_dados`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Não foi possível replicar os dados');
        }

        const resultado = await response.json();
        cliente.total_uploads = resultado.total_uploads ?? cliente.total_uploads ?? 0;
        refreshClientesUI(cliente.id);
    } finally {
        if (triggerButton instanceof HTMLElement) {
            triggerButton.disabled = false;
            triggerButton.innerHTML = originalHTML;
        }
    }
}

async function entrarCliente(event, id) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const cliente = clientes.find(c => c.id === id);
    if (!cliente) return;

    const branding = obterBrandingCliente(cliente);
    let triggerButton = null;

    if (event && event.currentTarget instanceof HTMLElement) {
        triggerButton = event.currentTarget;
    } else {
        triggerButton = document.querySelector(`.cliente-card[data-cliente-id="${id}"] .btn-card-primary`);
    }

    try {
        salvarSelecaoCliente(cliente, branding);
        atualizarSelecaoVisual(cliente.id);
        window.location.href = '/';
    } catch (error) {
        console.error('Erro ao selecionar cliente:', error);
        mostrarErro(error.message);
    }
}

function selecionarCliente(id) {
    entrarCliente(null, id);
}

function selecionarClienteTabela(id) {
    entrarCliente(null, id);
}

// ==================== MODAL ====================
function abrirModalNovo() {
    clienteEditando = null;
    document.getElementById('modalTitle').textContent = 'Novo Cliente';
    document.getElementById('formCliente').reset();
    document.getElementById('clienteId').value = '';
    resetLogoPreview('', gerarIniciais('Novo Cliente'));
    
    // Inicializa cores para novo cliente
    setTimeout(() => {
        sincronizarCores();
        aplicarCoresPadrao();
        // Scroll para a seção de cores se existir
        const secaoCores = document.getElementById('secaoCores');
        if (secaoCores) {
            setTimeout(() => {
                secaoCores.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 500);
        } else {
            console.warn('Seção de cores não encontrada!');
        }
    }, 300);
    
    document.getElementById('modalCliente').classList.add('show');
    document.getElementById('cnpj').focus();
}

function abrirModalEditar(id) {
    clienteEditando = id;
    document.getElementById('modalTitle').textContent = 'Editar Cliente';
    document.getElementById('formCliente').reset();
    document.getElementById('clienteId').value = id;
    
    const cliente = clientes.find(c => c.id === id);
    if (!cliente) {
        mostrarErro('Cliente não encontrado');
        return;
    }
    
    carregarDadosCliente(id);
}

async function carregarDadosCliente(id) {
    try {
        const response = await fetch(`/api/clientes/${id}`);
        if (!response.ok) throw new Error('Erro ao carregar dados do cliente');
        
        const cliente = await response.json();
        
        document.getElementById('cnpj').value = formatarCNPJExibicao(cliente.cnpj);
        document.getElementById('nome').value = cliente.nome || '';
        document.getElementById('nome_fantasia').value = cliente.nome_fantasia || '';
        document.getElementById('situacao').value = cliente.situacao || '';
        document.getElementById('data_abertura').value = cliente.data_abertura || '';
        document.getElementById('atividade_principal').value = cliente.atividade_principal || '';
        document.getElementById('inscricao_estadual').value = cliente.inscricao_estadual || '';
        document.getElementById('inscricao_municipal').value = cliente.inscricao_municipal || '';
        document.getElementById('cep').value = cliente.cep || '';
        document.getElementById('endereco').value = cliente.endereco || '';
        document.getElementById('numero').value = cliente.numero || '';
        document.getElementById('complemento').value = cliente.complemento || '';
        document.getElementById('bairro').value = cliente.bairro || '';
        document.getElementById('cidade').value = cliente.cidade || '';
        document.getElementById('estado').value = cliente.estado || '';
        document.getElementById('telefone').value = cliente.telefone || '';
        document.getElementById('email').value = cliente.email || '';

        const iniciaisLogo = gerarIniciais(cliente.nome_fantasia || cliente.nome || '');
        resetLogoPreview(cliente.logo_url || '', iniciaisLogo);
        
        // Carrega cores do cliente
        setTimeout(() => {
            sincronizarCores();
            carregarCoresClienteModal(id);
            // Scroll para a seção de cores se existir
            const secaoCores = document.getElementById('secaoCores');
            if (secaoCores) {
                setTimeout(() => {
                    secaoCores.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 500);
            } else {
                console.warn('Seção de cores não encontrada!');
            }
        }, 300);
        
        document.getElementById('modalCliente').classList.add('show');
    } catch (error) {
        console.error('Erro ao carregar dados do cliente:', error);
        mostrarErro('Erro ao carregar dados do cliente: ' + error.message);
    }
}

function fecharModal() {
    document.getElementById('modalCliente').classList.remove('show');
    clienteEditando = null;
    document.getElementById('formCliente').reset();
    resetLogoPreview('', gerarIniciais('Cliente'));
}

function editarCliente(id) {
    abrirModalEditar(id);
}

// ==================== BUSCAR CNPJ ====================
async function buscarCNPJ() {
    const cnpjInput = document.getElementById('cnpj');
    const cnpj = cnpjInput.value.replace(/\D/g, '');
    const btnBuscar = document.getElementById('btnBuscarCNPJ');
    
    if (cnpj.length !== 14) {
        alert('CNPJ deve ter 14 dígitos');
        return;
    }
    
    btnBuscar.disabled = true;
    btnBuscar.innerHTML = '<span class="loading-spinner"></span> Buscando...';
    
    try {
        const response = await fetch(`/api/buscar-cnpj/${cnpj}`);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao buscar CNPJ');
        }
        
        const dados = await response.json();
        
        document.getElementById('nome').value = dados.nome || '';
        document.getElementById('nome_fantasia').value = dados.nome_fantasia || '';
        document.getElementById('situacao').value = dados.situacao || '';
        document.getElementById('data_abertura').value = dados.data_abertura ? formatarDataParaInput(dados.data_abertura) : '';
        document.getElementById('atividade_principal').value = dados.atividade_principal || '';
        document.getElementById('inscricao_estadual').value = dados.inscricao_estadual || '';
        document.getElementById('inscricao_municipal').value = dados.inscricao_municipal || '';
        document.getElementById('cep').value = dados.cep || '';
        document.getElementById('endereco').value = dados.endereco || '';
        document.getElementById('numero').value = dados.numero || '';
        document.getElementById('complemento').value = dados.complemento || '';
        document.getElementById('bairro').value = dados.bairro || '';
        document.getElementById('cidade').value = dados.cidade || '';
        document.getElementById('estado').value = dados.estado || '';
        document.getElementById('telefone').value = dados.telefone || '';
        document.getElementById('email').value = dados.email || '';
        
        atualizarIniciaisLogoSeNecessario(true);
        mostrarSucesso('Dados da empresa carregados com sucesso!');
    } catch (error) {
        console.error('Erro ao buscar CNPJ:', error);
        mostrarErro('Erro ao buscar CNPJ: ' + error.message);
    } finally {
        btnBuscar.disabled = false;
        btnBuscar.innerHTML = '<i class="fas fa-search"></i> Buscar';
    }
}

// ==================== SALVAR CLIENTE ====================
async function salvarCliente(event) {
    event.preventDefault();
    
    const formData = {
        nome: document.getElementById('nome').value,
        cnpj: document.getElementById('cnpj').value,
        nome_fantasia: document.getElementById('nome_fantasia').value,
        logo_url: logoRemoverSelecionado ? '' : (document.getElementById('logoUrl').value || null),
        inscricao_estadual: document.getElementById('inscricao_estadual').value,
        inscricao_municipal: document.getElementById('inscricao_municipal').value,
        cep: document.getElementById('cep').value,
        endereco: document.getElementById('endereco').value,
        numero: document.getElementById('numero').value,
        complemento: document.getElementById('complemento').value,
        bairro: document.getElementById('bairro').value,
        cidade: document.getElementById('cidade').value,
        estado: document.getElementById('estado').value,
        telefone: document.getElementById('telefone').value,
        email: document.getElementById('email').value,
        situacao: document.getElementById('situacao').value,
        data_abertura: document.getElementById('data_abertura').value,
        atividade_principal: document.getElementById('atividade_principal').value
    };
    
    const clienteId = document.getElementById('clienteId').value;
    const url = clienteId ? `/api/clientes/${clienteId}` : '/api/clientes';
    const method = clienteId ? 'PUT' : 'POST';
    
    try {
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao salvar cliente');
        }
        
        const resultado = await response.json();
        const clienteIdFinal = clienteId || resultado.id;

        try {
            if (logoArquivoSelecionado) {
                await enviarLogoCliente(clienteIdFinal);
            }
        } catch (uploadErro) {
            console.error('Erro ao enviar logo:', uploadErro);
            mostrarErro('Cliente salvo, mas ocorreu erro ao enviar o logo: ' + uploadErro.message);
        }

        fecharModal();
        await carregarClientes();

        mostrarSucesso(resultado.message || 'Cliente salvo com sucesso!');
    } catch (error) {
        console.error('Erro ao salvar cliente:', error);
        mostrarErro('Erro ao salvar cliente: ' + error.message);
    }
}

// ==================== DELETAR CLIENTE ====================
async function confirmarDeletar(id) {
    const cliente = clientes.find(c => c.id === id);
    if (!cliente) return;

    if (cliente.situacao && cliente.situacao.toUpperCase() === 'ARQUIVO MORTO') {
        if (!confirm('Deseja ativar novamente este cliente?')) {
            return;
        }
        await ativarCliente(id);
    } else if ((cliente.total_uploads || 0) > 0) {
        if (!confirm('Este cliente possui dados cadastrados. Deseja mover para o arquivo morto?')) {
            return;
        }
        await arquivarCliente(id);
    } else {
        if (!confirm('Deseja excluir definitivamente este cliente? Esta ação não pode ser desfeita.')) {
        return;
        }
        await deletarCliente(id);
    }
    }
    
async function deletarCliente(id) {
    try {
        const response = await fetch(`/api/clientes/${id}`, { method: 'DELETE' });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao deletar cliente');
        }
        
        mostrarSucesso('Cliente deletado com sucesso!');
        carregarClientes();
    } catch (error) {
        console.error('Erro ao deletar cliente:', error);
        mostrarErro(error.message || 'Erro ao deletar cliente.');
    }
}

async function arquivarCliente(id) {
    try {
        const response = await fetch(`/api/clientes/${id}/arquivar`, { method: 'POST' });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao mover para arquivo morto');
        }

        mostrarSucesso('Cliente movido para arquivo morto.');
        carregarClientes();
    } catch (error) {
        console.error('Erro ao arquivar cliente:', error);
        mostrarErro(error.message || 'Erro ao mover para arquivo morto.');
    }
}

async function ativarCliente(id) {
    try {
        const response = await fetch(`/api/clientes/${id}/ativar`, { method: 'POST' });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao ativar cliente');
        }

        mostrarSucesso('Cliente reativado com sucesso.');
        carregarClientes();
    } catch (error) {
        console.error('Erro ao ativar cliente:', error);
        mostrarErro(error.message || 'Erro ao ativar cliente.');
    }
}
// ==================== FORMATAÇÃO ====================
function formatarCNPJ(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length <= 14) {
        value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
    }
    input.value = value;
}

function formatarCNPJExibicao(cnpj) {
    if (!cnpj) return '';
    const limpo = cnpj.replace(/\D/g, '');
    if (limpo.length === 14) {
        return limpo.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
    }
    return cnpj;
}

function formatarCEP(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length <= 8) {
        value = value.replace(/^(\d{5})(\d{3})$/, '$1-$2');
    }
    input.value = value;
}

function formatarTelefone(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length <= 11) {
        if (value.length <= 10) {
            value = value.replace(/^(\d{2})(\d{4})(\d{4})$/, '($1) $2-$3');
        } else {
            value = value.replace(/^(\d{2})(\d{5})(\d{4})$/, '($1) $2-$3');
        }
    }
    input.value = value;
}

function formatarDataParaInput(data) {
    if (data.includes('/')) {
        const [dia, mes, ano] = data.split('/');
        return `${ano}-${mes}-${dia}`;
    }
    return data;
}

function formatarDataCurta(isoString) {
    if (!isoString) return '-';
    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleDateString('pt-BR');
}

// ==================== UTILITÁRIOS ====================
function mostrarSucesso(mensagem) {
    alert(mensagem);
}

function mostrarErro(mensagem) {
    alert('Erro: ' + mensagem);
}

function gerarIniciais(str) {
    if (!str) return 'C';
    const partes = str.trim().split(/\s+/).filter(Boolean);
    if (partes.length === 1) {
        return partes[0].substring(0, 2).toUpperCase();
    }
    return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
}

// Expor funções necessárias globalmente
window.editarCliente = editarCliente;
window.selecionarCliente = selecionarCliente;
window.selecionarClienteTabela = selecionarClienteTabela;
window.entrarCliente = entrarCliente;
window.buscarCNPJ = buscarCNPJ;
window.salvarCliente = salvarCliente;
window.confirmarDeletar = confirmarDeletar;
window.abrirModalNovo = abrirModalNovo;
window.arquivarCliente = arquivarCliente;
window.removerLogoSelecionado = removerLogoSelecionado;

// ==================== GERENCIAMENTO DE CORES ====================
function sincronizarCores() {
    console.log('Sincronizando cores...');
    // Sincroniza color picker com text input
    const cores = ['Primary', 'PrimaryDark', 'PrimaryLight', 'Secondary', 'SecondaryDark', 'SecondaryLight'];
    let encontrados = 0;
    cores.forEach(cor => {
        const picker = document.getElementById(`cor${cor}`);
        const text = document.getElementById(`cor${cor}Text`);
        if (picker && text) {
            encontrados++;
            // Remove listeners antigos se existirem
            const novoPicker = picker.cloneNode(true);
            picker.parentNode.replaceChild(novoPicker, picker);
            const novoText = text.cloneNode(true);
            text.parentNode.replaceChild(novoText, text);
            
            // Adiciona novos listeners
            novoPicker.addEventListener('input', (e) => {
                novoText.value = e.target.value.toUpperCase();
            });
            novoText.addEventListener('input', (e) => {
                const valor = e.target.value;
                if (/^#[0-9A-F]{6}$/i.test(valor)) {
                    novoPicker.value = valor;
                }
            });
        }
    });
    console.log(`Elementos de cores encontrados: ${encontrados}/${cores.length}`);
}

async function carregarCoresClienteModal(clienteId) {
    console.log('Carregando cores para cliente:', clienteId);
    
    // Verifica se os elementos existem
    const corPrimary = document.getElementById('corPrimary');
    if (!corPrimary) {
        console.error('Elementos de cores não encontrados no DOM!');
        return;
    }
    
    if (!clienteId) {
        aplicarCoresPadrao();
        return;
    }
    
    try {
        const response = await fetch(`/api/clientes/${clienteId}/cores`);
        if (!response.ok) {
            aplicarCoresPadrao();
            return;
        }
        
        const data = await response.json();
        if (data.success && data.cores) {
            document.getElementById('corPrimary').value = data.cores.primary || '#1a237e';
            document.getElementById('corPrimaryText').value = (data.cores.primary || '#1a237e').toUpperCase();
            document.getElementById('corPrimaryDark').value = data.cores.primaryDark || '#0d47a1';
            document.getElementById('corPrimaryDarkText').value = (data.cores.primaryDark || '#0d47a1').toUpperCase();
            document.getElementById('corPrimaryLight').value = data.cores.primaryLight || '#3949ab';
            document.getElementById('corPrimaryLightText').value = (data.cores.primaryLight || '#3949ab').toUpperCase();
            document.getElementById('corSecondary').value = data.cores.secondary || '#556B2F';
            document.getElementById('corSecondaryText').value = (data.cores.secondary || '#556B2F').toUpperCase();
            document.getElementById('corSecondaryDark').value = data.cores.secondaryDark || '#4a5d23';
            document.getElementById('corSecondaryDarkText').value = (data.cores.secondaryDark || '#4a5d23').toUpperCase();
            document.getElementById('corSecondaryLight').value = data.cores.secondaryLight || '#6B8E23';
            document.getElementById('corSecondaryLightText').value = (data.cores.secondaryLight || '#6B8E23').toUpperCase();
            console.log('Cores carregadas com sucesso');
        } else {
            aplicarCoresPadrao();
        }
    } catch (error) {
        console.error('Erro ao carregar cores:', error);
        aplicarCoresPadrao();
    }
}

function aplicarCoresPadrao() {
    document.getElementById('corPrimary').value = '#1a237e';
    document.getElementById('corPrimaryText').value = '#1A237E';
    document.getElementById('corPrimaryDark').value = '#0d47a1';
    document.getElementById('corPrimaryDarkText').value = '#0D47A1';
    document.getElementById('corPrimaryLight').value = '#3949ab';
    document.getElementById('corPrimaryLightText').value = '#3949AB';
    document.getElementById('corSecondary').value = '#556B2F';
    document.getElementById('corSecondaryText').value = '#556B2F';
    document.getElementById('corSecondaryDark').value = '#4a5d23';
    document.getElementById('corSecondaryDarkText').value = '#4A5D23';
    document.getElementById('corSecondaryLight').value = '#6B8E23';
    document.getElementById('corSecondaryLightText').value = '#6B8E23';
}

async function salvarCoresCliente() {
    const clienteId = document.getElementById('clienteId').value;
    if (!clienteId) {
        alert('Salve o cliente primeiro antes de configurar as cores');
        return;
    }
    
    const cores = {
        primary: document.getElementById('corPrimary').value,
        primaryDark: document.getElementById('corPrimaryDark').value,
        primaryLight: document.getElementById('corPrimaryLight').value,
        secondary: document.getElementById('corSecondary').value,
        secondaryDark: document.getElementById('corSecondaryDark').value,
        secondaryLight: document.getElementById('corSecondaryLight').value,
        // Gera paleta automaticamente
        paleta: [
            document.getElementById('corPrimary').value,
            document.getElementById('corSecondary').value,
            document.getElementById('corPrimaryDark').value,
            document.getElementById('corSecondaryLight').value,
            document.getElementById('corPrimaryLight').value,
            document.getElementById('corSecondaryDark').value
        ]
    };
    
    try {
        const response = await fetch(`/api/clientes/${clienteId}/cores`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cores })
        });
        
        if (!response.ok) {
            throw new Error('Erro ao salvar cores');
        }
        
        const data = await response.json();
        if (data.success) {
            alert('Cores salvas com sucesso! Os gráficos serão atualizados automaticamente.');
            // Recarrega cores se o cliente estiver selecionado
            if (typeof carregarCoresCliente === 'function') {
                await carregarCoresCliente(clienteId);
            }
        }
    } catch (error) {
        console.error('Erro ao salvar cores:', error);
        alert('Erro ao salvar cores. Tente novamente.');
    }
}

// Sincroniza cores quando cria novo cliente
const originalAbrirModalNovo = window.abrirModalNovo;
window.abrirModalNovo = function() {
    originalAbrirModalNovo();
    setTimeout(() => {
        sincronizarCores();
        aplicarCoresPadrao();
    }, 100);
};

window.aplicarCoresPadrao = aplicarCoresPadrao;
window.salvarCoresCliente = salvarCoresCliente;

