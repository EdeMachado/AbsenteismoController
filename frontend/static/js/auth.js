/**
 * Sistema de autenticação e layout do painel
 */

// Tema escuro desabilitado - sempre remove o atributo
(function() {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('tema_escuro', 'false');
})();

const DEFAULT_THEME = {
    primary: '#1a237e',
    primaryDark: '#0d47a1',
    primaryLight: '#3949ab',
    secondary: '#556B2F',
    secondaryLight: '#6B8E23',
    background: '#F5F7FA',
    logo: null
};

const SIDEBAR_MENU_ITEMS = [
    { path: '/', icon: 'fas fa-gauge-high', label: 'Dashboard' },
    { path: '/dados_powerbi', icon: 'fas fa-table', label: 'Meus Dados' },
    { path: '/produtividade', icon: 'fas fa-chart-line', label: 'Produtividade' },
    { path: '/upload', icon: 'fas fa-cloud-arrow-up', label: 'Upload Mensal' },
    { path: '/apresentacao', icon: 'fas fa-tv', label: 'Apresentação' },
    // Relatórios removido - exportação agora está na apresentação
    { path: '/funcionarios', icon: 'fas fa-user-group', label: 'Funcionários' },
    { path: '/comparativos', icon: 'fas fa-chart-column', label: 'Comparativos' },
    { path: '/configuracoes', icon: 'fas fa-gear', label: 'Configurações' }
];

function normalizePath(path) {
    if (!path) return '/';
    if (path.length > 1 && path.endsWith('/')) {
        return path.slice(0, -1);
    }
    return path;
}

function getCurrentPath() {
    return normalizePath(window.location.pathname);
}

function getCurrentClientId(defaultId = null) {
    const stored = Number(localStorage.getItem('cliente_selecionado'));
    return Number.isFinite(stored) && stored > 0 ? stored : defaultId;
}

window.getCurrentClientId = getCurrentClientId;

function renderSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    const currentPath = getCurrentPath();
    const clientId = getCurrentClientId(null);
    const clienteNome = localStorage.getItem('cliente_nome') || '';
    const clienteCnpj = localStorage.getItem('cliente_cnpj');
    const clienteInicial = gerarIniciais(clienteNome || 'Cliente');
    const theme = applyCurrentClientTheme();
    
    // Adiciona classe para Roda de Ouro (client_id = 4) - menu preto
    if (clientId === 4) {
        sidebar.classList.add('roda-ouro-sidebar');
        sidebar.classList.remove('converplast-sidebar');
    } 
    // Adiciona classe para Converplast (client_id = 2) - menu azul
    else if (clientId === 2) {
        sidebar.classList.add('converplast-sidebar');
        sidebar.classList.remove('roda-ouro-sidebar');
    } 
    // Remove classes especiais para outros clientes
    else {
        sidebar.classList.remove('roda-ouro-sidebar');
        sidebar.classList.remove('converplast-sidebar');
    }

    sidebar.innerHTML = `
        <div class="sidebar-scroll">
            <div class="sidebar-scroll-inner">
                <div class="sidebar-header">
                    <div class="sidebar-brand">
                        <span class="sidebar-brand-icon"><i class="fas fa-chart-line"></i></span>
                        <div class="sidebar-brand-info">
                            <strong>AbsenteismoController</strong>
                            <span>Inteligência GrupoBioMed</span>
                        </div>
                    </div>
                </div>
                <div class="sidebar-current-client ${clienteNome ? '' : 'empty'}">
                    <div class="sidebar-current-client-main">
                        <div class="client-avatar">
                            ${(() => {
                                const logoUrl = localStorage.getItem('cliente_logo_url');
                                if (logoUrl) {
                                    return `<img src="${logoUrl}" alt="Logo ${clienteNome || ''}" onerror="this.remove();" />`;
                                }
                                return clienteNome ? clienteInicial : '<i class="fas fa-briefcase"></i>';
                            })()}
                        </div>
                        <div class="client-info">
                            <span class="client-label">${clienteNome ? 'Cliente atual' : 'Nenhum cliente selecionado'}</span>
                            <strong>${clienteNome || 'Selecione um cliente'}</strong>
                            ${clienteNome && clienteCnpj ? `<span class="client-meta">${formatarCNPJ(clienteCnpj)}</span>` : ''}
                        </div>
                    </div>
                    <button class="btn btn-secondary btn-sm" onclick="trocarCliente(event)">
                        <i class="fas fa-arrows-rotate"></i> Trocar cliente
                    </button>
                </div>
                <nav class="sidebar-nav no-title">
                    ${SIDEBAR_MENU_ITEMS.map(item => {
                        const itemPath = normalizePath(item.path);
                        const isActive = currentPath === itemPath || (itemPath !== '/' && currentPath.startsWith(itemPath));
                        // Adiciona classe especial para Dashboard se for Roda de Ouro
                        const isRodaOuroDashboard = clientId === 4 && item.label === 'Dashboard' && isActive;
                        return `
                            <a href="${item.path}" class="nav-item${isActive ? ' active' : ''}${isRodaOuroDashboard ? ' roda-ouro-dashboard' : ''}">
                                <span class="nav-item-icon"><i class="${item.icon}"></i></span>
                                <span class="nav-item-text">
                                    <span class="nav-item-title">${item.label}</span>
                                </span>
                                <i class="fas fa-angle-right nav-item-chevron"></i>
                            </a>
                        `;
                    }).join('')}
                </nav>
            </div>
        </div>
        <div class="sidebar-bottom"></div>
    `;
    
    // Aplica cor dourada ao Dashboard se for Roda de Ouro
    if (clientId === 4) {
        setTimeout(() => {
            const navItems = document.querySelectorAll('.nav-item');
            navItems.forEach(item => {
                const span = item.querySelector('.nav-item-title');
                if (span && span.textContent.trim() === 'Dashboard' && item.classList.contains('active')) {
                    item.classList.add('roda-ouro-dashboard');
                }
            });
        }, 50);
    }
}

// Verifica se está autenticado
function isAuthenticated() {
    return localStorage.getItem('access_token') !== null;
}

// Obtém token de acesso
function getAccessToken() {
    return localStorage.getItem('access_token');
}

// Obtém usuário atual
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// Verifica se é admin
function isAdmin() {
    const user = getCurrentUser();
    return user && user.is_admin;
}

// Faz logout
async function logout() {
    try {
        const token = getAccessToken();
        if (token) {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        }
    } catch (error) {
        console.error('Erro ao fazer logout:', error);
    } finally {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    }
}

// Adiciona token de autorização aos headers
function getAuthHeaders() {
    const token = getAccessToken();
    return token ? {
        'Authorization': `Bearer ${token}`
    } : {};
}

// Verifica autenticação e redireciona se necessário
function checkAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Verifica se é admin e redireciona se necessário
function checkAdmin() {
    if (!checkAuth()) return false;
    if (!isAdmin()) {
        alert('Acesso negado. Apenas administradores podem acessar esta página.');
        window.location.href = '/';
        return false;
    }
    return true;
}

// Intercepta fetch para adicionar token automaticamente
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    // Se não for uma requisição de autenticação, adiciona token
    if (!url.includes('/api/auth/login') && !url.includes('/api/health') && !url.includes('/landing')) {
        const token = getAccessToken();
        if (token) {
            options.headers = options.headers || {};
            options.headers['Authorization'] = `Bearer ${token}`;
        }
    }
    return originalFetch.call(this, url, options);
};

// Exibe informações do usuário
function displayUserInfo() {
    renderHeaderUser();
    if (isAdmin()) {
        const adminSection = document.getElementById('adminSection');
        if (adminSection) {
            adminSection.style.display = 'block';
        }
    }
}

function renderHeaderUser() {
    const headerActions = document.querySelector('.header .header-actions') || document.querySelector('.header');
    if (!headerActions) return;

    let container = headerActions.querySelector('#headerUserWidget');
    if (!container) {
        container = document.createElement('div');
        container.id = 'headerUserWidget';
        container.className = 'header-user-widget';
        headerActions.appendChild(container);
    }

    const user = getCurrentUser();
    if (!user) {
        container.innerHTML = `
            <a href="/login" class="btn btn-secondary btn-sm header-login-btn">
                <i class="fas fa-sign-in-alt"></i> Entrar
            </a>
        `;
        return;
    }

    const initials = getUserInitials(user);
    container.innerHTML = `
        <div class="header-user-info">
            <div class="header-user-avatar">${initials}</div>
            <div class="header-user-text">
                <strong>${user.nome_completo || user.username}</strong>
                ${user.email ? `<span>${user.email}</span>` : ''}
            </div>
            <button class="btn btn-secondary btn-sm header-logout-btn" onclick="logout()">
                <i class="fas fa-sign-out-alt"></i>
            </button>
        </div>
    `;
}

function getUserInitials(user) {
    const source = (user && (user.nome_completo || user.username || '')).trim();
    if (!source) return 'US';
    const parts = source.split(/\s+/).filter(Boolean);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// Verifica autenticação ao carregar página (exceto login e landing)
if (!window.location.pathname.includes('/login') && 
    !window.location.pathname.includes('/landing') &&
    !window.location.pathname.includes('/api/')) {
    if (!checkAuth()) {
        // Redireciona para login
    } else {
        const boot = () => {
            // Tema escuro desabilitado - sempre remove
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('tema_escuro', 'false');
            applyCurrentClientTheme();
            renderSidebar();
            displayUserInfo();
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', boot, { once: true });
        } else {
            boot();
        }
    }
}

function getStoredClientTheme() {
    try {
        const stored = localStorage.getItem('cliente_tema');
        return stored ? JSON.parse(stored) : null;
    } catch (error) {
        console.warn('Tema de cliente inválido:', error);
        return null;
    }
}

function setThemeVariables(theme) {
    const root = document.documentElement;
    const finalTheme = { ...DEFAULT_THEME, ...(theme || {}) };
    
    root.style.setProperty('--primary', finalTheme.primary);
    root.style.setProperty('--primary-dark', finalTheme.primaryDark || finalTheme.primary);
    root.style.setProperty('--primary-light', finalTheme.primaryLight || finalTheme.primary);
    root.style.setProperty('--secondary', finalTheme.secondary || DEFAULT_THEME.secondary);
    root.style.setProperty('--secondary-light', finalTheme.secondaryLight || DEFAULT_THEME.secondaryLight);
    if (finalTheme.background) {
        root.style.setProperty('--background', finalTheme.background);
    }
}

function applyCurrentClientTheme() {
    const theme = getStoredClientTheme() || DEFAULT_THEME;
    setThemeVariables(theme);
    return theme;
}

// Tema escuro desabilitado - função sempre remove o tema
function aplicarTemaEscuroGlobal() {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('tema_escuro', 'false');
}

function gerarIniciais(nome) {
    if (!nome) return 'C';
    const partes = nome.split(' ').filter(Boolean);
    if (partes.length === 1) {
        return partes[0].substring(0, 2).toUpperCase();
    }
    return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
}

function formatarCNPJ(cnpj) {
    if (!cnpj) return '';
    const limpo = cnpj.replace(/\D/g, '');
    if (limpo.length !== 14) return cnpj;
    return limpo.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
}

function trocarCliente(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    localStorage.removeItem('cliente_selecionado');
    localStorage.removeItem('cliente_nome');
    localStorage.removeItem('cliente_cnpj');
    localStorage.removeItem('cliente_tema');
    window.location.href = '/clientes';
}

window.applyCurrentClientTheme = applyCurrentClientTheme;
window.trocarCliente = trocarCliente;

// Listener para atualizar sidebar quando cliente mudar
if (typeof window !== 'undefined') {
    // Observa mudanças no localStorage
    window.addEventListener('storage', (e) => {
        if (e.key === 'cliente_selecionado') {
            // Atualiza sidebar quando cliente muda
            setTimeout(() => {
                if (typeof renderSidebar === 'function') {
                    renderSidebar();
                }
            }, 100);
        }
    });
    
    // Intercepta setItem para detectar mudanças na mesma aba
    const originalSetItem = Storage.prototype.setItem;
    Storage.prototype.setItem = function(key, value) {
        originalSetItem.call(this, key, value);
        if (key === 'cliente_selecionado') {
            // Dispara evento customizado
            window.dispatchEvent(new Event('storage'));
            // Atualiza sidebar
            setTimeout(() => {
                if (typeof renderSidebar === 'function') {
                    renderSidebar();
                }
            }, 100);
        }
    };
}

