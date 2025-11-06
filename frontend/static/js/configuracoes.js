/**
 * Página de Configurações
 */

let configData = {};
let usersData = [];

// Carrega configurações
async function carregarConfiguracoes() {
    try {
        const response = await fetch('/api/config');
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error('Erro ao carregar configurações');
        }
        
        configData = await response.json();
        
        // Preenche campos (usa valores padrão se não existirem)
        const nomeSistemaEl = document.getElementById('nome_sistema');
        const empresaEl = document.getElementById('empresa');
        const emailContatoEl = document.getElementById('email_contato');
        const itensPorPaginaEl = document.getElementById('itens_por_pagina');
        const temaEscuroEl = document.getElementById('tema_escuro');
        
        if (nomeSistemaEl) nomeSistemaEl.value = configData.nome_sistema?.valor || 'AbsenteismoController';
        if (empresaEl) empresaEl.value = configData.empresa?.valor || '';
        if (emailContatoEl) emailContatoEl.value = configData.email_contato?.valor || '';
        if (itensPorPaginaEl) itensPorPaginaEl.value = configData.itens_por_pagina?.valor || '50';
        if (temaEscuroEl) temaEscuroEl.checked = configData.tema_escuro?.valor === true || configData.tema_escuro?.valor === 'true';
        
    } catch (error) {
        console.error('Erro:', error);
        mostrarAlert('Erro ao carregar configurações', 'error');
    }
}

// Salva configurações
async function salvarConfiguracoes() {
    try {
        if (!isAdmin()) {
            mostrarAlert('Apenas administradores podem alterar configurações', 'error');
            return;
        }
        
        const configs = [
            { chave: 'nome_sistema', valor: document.getElementById('nome_sistema').value },
            { chave: 'empresa', valor: document.getElementById('empresa').value },
            { chave: 'email_contato', valor: document.getElementById('email_contato').value },
            { chave: 'itens_por_pagina', valor: document.getElementById('itens_por_pagina').value },
            { chave: 'tema_escuro', valor: document.getElementById('tema_escuro').checked.toString(), tipo: 'boolean' }
        ];
        
        for (const config of configs) {
            const formData = new FormData();
            formData.append('valor', config.valor);
            formData.append('tipo', config.tipo || 'string');
            
            const response = await fetch(`/api/config/${config.chave}`, {
                method: 'PUT',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Erro ao salvar ${config.chave}`);
            }
        }
        
        mostrarAlert('Configurações salvas com sucesso!', 'success');
        
    } catch (error) {
        console.error('Erro:', error);
        mostrarAlert('Erro ao salvar configurações', 'error');
    }
}

// Carrega usuários (apenas admin)
async function carregarUsuarios() {
    if (!isAdmin()) return;
    
    try {
        const response = await fetch('/api/users');
        if (!response.ok) {
            throw new Error('Erro ao carregar usuários');
        }
        
        usersData = await response.json();
        renderizarUsuarios();
        
    } catch (error) {
        console.error('Erro:', error);
        mostrarAlert('Erro ao carregar usuários', 'error');
    }
}

// Renderiza tabela de usuários
function renderizarUsuarios() {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;
    
    if (usersData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum usuário encontrado</td></tr>';
        return;
    }
    
    tbody.innerHTML = usersData.map(user => `
        <tr>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${user.nome_completo || '-'}</td>
            <td>
                <span class="badge ${user.is_admin ? 'badge-primary' : 'badge-secondary'}">
                    ${user.is_admin ? 'Sim' : 'Não'}
                </span>
            </td>
            <td>
                <span class="badge ${user.is_active ? 'badge-success' : 'badge-danger'}">
                    ${user.is_active ? 'Ativo' : 'Inativo'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="editarUsuario(${user.id})" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Mostra modal de novo usuário
function mostrarModalNovoUsuario() {
    document.getElementById('modalNovoUsuario').style.display = 'flex';
    // Limpa campos
    document.getElementById('novo_username').value = '';
    document.getElementById('novo_email').value = '';
    document.getElementById('novo_password').value = '';
    document.getElementById('novo_nome_completo').value = '';
    document.getElementById('novo_is_admin').checked = false;
}

// Fecha modal
function fecharModalNovoUsuario() {
    document.getElementById('modalNovoUsuario').style.display = 'none';
}

// Cria novo usuário
async function criarUsuario() {
    try {
        const formData = new FormData();
        formData.append('username', document.getElementById('novo_username').value);
        formData.append('email', document.getElementById('novo_email').value);
        formData.append('password', document.getElementById('novo_password').value);
        formData.append('nome_completo', document.getElementById('novo_nome_completo').value);
        formData.append('is_admin', document.getElementById('novo_is_admin').checked.toString());
        
        const response = await fetch('/api/users', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao criar usuário');
        }
        
        mostrarAlert('Usuário criado com sucesso!', 'success');
        fecharModalNovoUsuario();
        carregarUsuarios();
        
    } catch (error) {
        console.error('Erro:', error);
        mostrarAlert(error.message || 'Erro ao criar usuário', 'error');
    }
}

// Editar usuário
function editarUsuario(userId) {
    const user = usersData.find(u => u.id === userId);
    if (!user) return;
    
    mostrarAlert('Funcionalidade de edição em desenvolvimento', 'info');
}

// Mostra alerta
function mostrarAlert(message, type = 'info') {
    const alertDiv = document.getElementById('alert');
    if (!alertDiv) return;
    
    alertDiv.textContent = message;
    alertDiv.className = `alert alert-${type}`;
    alertDiv.style.display = 'block';
    
    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 5000);
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Aguarda auth.js carregar
    setTimeout(() => {
        if (typeof checkAuth === 'function' && checkAuth()) {
            carregarConfiguracoes();
            if (typeof isAdmin === 'function' && isAdmin()) {
                document.getElementById('adminSection').style.display = 'block';
                carregarUsuarios();
            }
        } else if (typeof isAuthenticated === 'function' && isAuthenticated()) {
            carregarConfiguracoes();
            if (typeof isAdmin === 'function' && isAdmin()) {
                document.getElementById('adminSection').style.display = 'block';
                carregarUsuarios();
            }
        } else {
            window.location.href = '/login';
        }
    }, 500);
});

