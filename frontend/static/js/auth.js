/**
 * Sistema de autenticação
 */

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
    const user = getCurrentUser();
    if (user) {
        const userNameElements = document.querySelectorAll('#userName');
        userNameElements.forEach(el => {
            el.textContent = user.nome_completo || user.username;
        });
        
        // Mostra seção admin se for admin
        if (isAdmin()) {
            const adminSection = document.getElementById('adminSection');
            if (adminSection) {
                adminSection.style.display = 'block';
            }
        }
    }
}

// Verifica autenticação ao carregar página (exceto login e landing)
if (!window.location.pathname.includes('/login') && 
    !window.location.pathname.includes('/landing') &&
    !window.location.pathname.includes('/api/')) {
    if (!checkAuth()) {
        // Redireciona para login
    } else {
        // Exibe informações do usuário
        document.addEventListener('DOMContentLoaded', displayUserInfo);
    }
}

