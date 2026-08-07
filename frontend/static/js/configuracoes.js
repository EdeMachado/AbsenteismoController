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
        
        if (nomeSistemaEl) nomeSistemaEl.value = configData.nome_sistema?.valor || 'BioMed Platform';
        if (empresaEl) empresaEl.value = configData.empresa?.valor || '';
        if (emailContatoEl) emailContatoEl.value = configData.email_contato?.valor || '';
        if (itensPorPaginaEl) itensPorPaginaEl.value = configData.itens_por_pagina?.valor || '50';
        // Tema escuro desabilitado - sempre remove o atributo
        if (temaEscuroEl) {
            temaEscuroEl.checked = false;
            aplicarTemaEscuro(false);
        }
        
    } catch (error) {
        console.error('Erro:', error);
        mostrarAlert('Erro ao carregar configurações', 'error');
    }
}

// Aplica tema escuro (função global)
function aplicarTemaEscuro(ativo) {
    const html = document.documentElement;
    if (ativo) {
        html.setAttribute('data-theme', 'dark');
        localStorage.setItem('tema_escuro', 'true');
    } else {
        html.removeAttribute('data-theme');
        localStorage.setItem('tema_escuro', 'false');
    }
}

// Torna função global
window.aplicarTemaEscuro = aplicarTemaEscuro;

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
            // Tema escuro desabilitado
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
        
        // Tema escuro desabilitado - sempre desativa
        aplicarTemaEscuro(false);
        
        mostrarAlert('Configurações salvas com sucesso!', 'success');
        
    } catch (error) {
        console.error('Erro:', error);
        mostrarAlert('Erro ao salvar configurações', 'error');
    }
}

// Carrega usuários (apenas admin)
async function carregarUsuarios() {
    // Verifica se é admin de várias formas
    let isUserAdmin = false;
    
    if (typeof isAdmin === 'function') {
        try {
            isUserAdmin = isAdmin();
        } catch (e) {
            console.warn('Erro ao verificar isAdmin:', e);
        }
    }
    
    if (typeof window.isAdmin === 'function') {
        try {
            isUserAdmin = window.isAdmin();
        } catch (e) {
            console.warn('Erro ao verificar window.isAdmin:', e);
        }
    }
    
    // Verifica no token JWT
    try {
        const token = localStorage.getItem('access_token');
        if (token) {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.is_admin === true) {
                isUserAdmin = true;
            }
        }
    } catch (e) {
        console.warn('Erro ao verificar token:', e);
    }
    
    if (!isUserAdmin) {
        console.log('⚠️ Usuário não é admin, não carregando usuários');
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.error('❌ Token não encontrado');
            const tbody = document.getElementById('usersTableBody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Token de autenticação não encontrado</td></tr>';
            }
            return;
        }
        
        console.log('🔑 Token encontrado, fazendo requisição para /api/users');
        console.log('🔑 Token (primeiros 20 chars):', token.substring(0, 20) + '...');
        
        // O interceptador em auth.js já adiciona o token, mas vamos garantir
        const response = await fetch('/api/users', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                console.error('❌ Não autorizado (401) - Token pode estar inválido ou expirado');
                const errorText = await response.text();
                console.error('Resposta do servidor:', errorText);
                const tbody = document.getElementById('usersTableBody');
                if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Não autorizado. Faça login novamente.</td></tr>';
                }
                return;
            }
            throw new Error(`Erro ${response.status} ao carregar usuários`);
        }
        
        usersData = await response.json();
        console.log('✅ Usuários carregados:', usersData.length);
        renderizarUsuarios();
        
    } catch (error) {
        console.error('❌ Erro ao carregar usuários:', error);
        const tbody = document.getElementById('usersTableBody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center">Erro: ${error.message}</td></tr>`;
        }
    }
}

// Renderiza tabela de usuários
function renderizarUsuarios() {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;
    
    if (usersData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum usuário encontrado</td></tr>';
        return;
    }
    
    tbody.innerHTML = usersData.map(user => {
        // Busca nome da empresa se tiver client_id
        let empresaNome = 'Todas';
        if (user.client_id && clientesList.length > 0) {
            const cliente = clientesList.find(c => c.id === user.client_id);
            if (cliente) {
                empresaNome = cliente.nome_fantasia || cliente.nome;
            }
        }
        
        return `
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
            <td>${empresaNome}</td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="window.editarUsuario(${user.id})" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                ${user.is_active ? `
                    <button class="btn btn-sm btn-danger" onclick="window.desativarUsuario(${user.id}, '${user.username.replace(/'/g, "\\'")}')" title="Desativar">
                        <i class="fas fa-ban"></i>
                    </button>
                ` : `
                    <button class="btn btn-sm btn-success" onclick="window.ativarUsuario(${user.id})" title="Ativar">
                        <i class="fas fa-check"></i>
                    </button>
                `}
                <button class="btn btn-sm btn-danger" onclick="window.excluirUsuario(${user.id}, '${user.username.replace(/'/g, "\\'")}')" title="Excluir" style="margin-left: 4px;">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `;
    }).join('');
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
    
    // Preenche select de clientes
    const selectClient = document.getElementById('novo_client_id');
    selectClient.innerHTML = '<option value="">Todas as empresas (acesso completo)</option>';
    
    clientesList.forEach(cliente => {
        const option = document.createElement('option');
        option.value = cliente.id;
        option.textContent = cliente.nome_fantasia || cliente.nome;
        selectClient.appendChild(option);
    });
    
    // Se não tiver clientes carregados, carrega agora
    if (clientesList.length === 0) {
        carregarClientes().then(() => {
            const selectClient = document.getElementById('novo_client_id');
            selectClient.innerHTML = '<option value="">Todas as empresas (acesso completo)</option>';
            clientesList.forEach(cliente => {
                const option = document.createElement('option');
                option.value = cliente.id;
                option.textContent = cliente.nome_fantasia || cliente.nome;
                selectClient.appendChild(option);
            });
        });
    }
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
        
        const clientId = document.getElementById('novo_client_id').value;
        if (clientId) {
            formData.append('client_id', clientId);
        }
        
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

// Variável global para armazenar lista de clientes
let clientesList = [];

// Carrega lista de clientes para o select
async function carregarClientes() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/clientes', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            clientesList = await response.json();
        }
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
    }
}

// Editar usuário
function editarUsuario(userId) {
    console.log('🔧 Editar usuário chamado:', userId);
    const user = usersData.find(u => u.id === userId);
    if (!user) {
        console.error('❌ Usuário não encontrado:', userId);
        mostrarAlert('Usuário não encontrado', 'error');
        return;
    }
    
    console.log('✅ Usuário encontrado:', user);
    
    // Preenche campos do modal
    const modal = document.getElementById('modalEditarUsuario');
    if (!modal) {
        console.error('❌ Modal não encontrado');
        mostrarAlert('Modal de edição não encontrado', 'error');
        return;
    }
    
    document.getElementById('editar_user_id').value = user.id;
    document.getElementById('editar_username').value = user.username || '';
    document.getElementById('editar_email').value = user.email || '';
    document.getElementById('editar_password').value = '';
    document.getElementById('editar_nome_completo').value = user.nome_completo || '';
    document.getElementById('editar_is_admin').checked = user.is_admin || false;
    document.getElementById('editar_is_active').checked = user.is_active !== false;
    
    // Preenche select de clientes
    const selectClient = document.getElementById('editar_client_id');
    selectClient.innerHTML = '<option value="">Todas as empresas (acesso completo)</option>';
    
    clientesList.forEach(cliente => {
        const option = document.createElement('option');
        option.value = cliente.id;
        option.textContent = cliente.nome_fantasia || cliente.nome;
        if (user.client_id === cliente.id) {
            option.selected = true;
        }
        selectClient.appendChild(option);
    });
    
    // Se não tiver clientes carregados, carrega agora
    if (clientesList.length === 0) {
        carregarClientes().then(() => {
            // Recarrega o select após carregar clientes
            const selectClient = document.getElementById('editar_client_id');
            selectClient.innerHTML = '<option value="">Todas as empresas (acesso completo)</option>';
            clientesList.forEach(cliente => {
                const option = document.createElement('option');
                option.value = cliente.id;
                option.textContent = cliente.nome_fantasia || cliente.nome;
                if (user.client_id === cliente.id) {
                    option.selected = true;
                }
                selectClient.appendChild(option);
            });
        });
    }
    
    // Mostra modal
    try {
        // Remove display: none inline se existir
        modal.removeAttribute('style');
        // Adiciona display flex
        modal.style.display = 'flex';
        modal.classList.add('show');
        console.log('✅ Modal exibido - display:', modal.style.display);
        
        // Verifica se realmente está visível
        setTimeout(() => {
            const isVisible = modal.offsetParent !== null || modal.style.display !== 'none';
            if (!isVisible) {
                console.error('❌ Modal não está visível após tentativa de exibir');
                alert('Erro: Modal não está aparecendo. Verifique o console (F12) para mais detalhes.');
            } else {
                console.log('✅ Modal confirmado como visível');
            }
        }, 100);
    } catch (e) {
        console.error('❌ Erro ao exibir modal:', e);
        alert('Erro ao abrir modal de edição: ' + e.message);
    }
}

// Garantir que função está disponível globalmente e sobrescrever qualquer versão antiga
// Define diretamente no window para garantir que está disponível
window.editarUsuario = editarUsuario;
window.salvarEdicaoUsuario = salvarEdicaoUsuario;
window.fecharModalEditarUsuario = fecharModalEditarUsuario;
window.excluirUsuario = excluirUsuario;
window.desativarUsuario = desativarUsuario;
window.ativarUsuario = ativarUsuario;

// Força sobrescrever qualquer função antiga que possa existir
console.log('✅ Funções registradas globalmente:', {
    editarUsuario: typeof window.editarUsuario,
    salvarEdicaoUsuario: typeof window.salvarEdicaoUsuario,
    excluirUsuario: typeof window.excluirUsuario
});

// Fecha modal de edição
function fecharModalEditarUsuario() {
    document.getElementById('modalEditarUsuario').style.display = 'none';
}

// Salva edição de usuário
async function salvarEdicaoUsuario() {
    console.log('💾 Salvar edição chamado');
    try {
        const userId = document.getElementById('editar_user_id').value;
        console.log('📝 User ID:', userId);
        if (!userId) {
            mostrarAlert('ID do usuário não encontrado', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('username', document.getElementById('editar_username').value);
        formData.append('email', document.getElementById('editar_email').value);
        
        const password = document.getElementById('editar_password').value;
        if (password && password.trim()) {
            formData.append('password', password);
        }
        
        formData.append('nome_completo', document.getElementById('editar_nome_completo').value || '');
        formData.append('is_admin', document.getElementById('editar_is_admin').checked ? 'true' : 'false');
        formData.append('is_active', document.getElementById('editar_is_active').checked ? 'true' : 'false');
        
        const clientId = document.getElementById('editar_client_id').value;
        if (clientId && clientId !== '') {
            formData.append('client_id', clientId);
        } else {
            formData.append('client_id', '');
        }
        
        console.log('📤 Enviando dados:', {
            username: formData.get('username'),
            email: formData.get('email'),
            is_admin: formData.get('is_admin'),
            client_id: formData.get('client_id')
        });
        
        const token = localStorage.getItem('access_token');
        if (!token) {
            throw new Error('Token de autenticação não encontrado');
        }
        
        const response = await fetch(`/api/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        console.log('📥 Resposta recebida:', response.status, response.statusText);
        
        if (!response.ok) {
            const error = await response.json();
            console.error('❌ Erro da API:', error);
            throw new Error(error.detail || 'Erro ao atualizar usuário');
        }
        
        const result = await response.json();
        console.log('✅ Sucesso:', result);
        
        mostrarAlert('Usuário atualizado com sucesso!', 'success');
        fecharModalEditarUsuario();
        carregarUsuarios();
        
    } catch (error) {
        console.error('❌ Erro completo:', error);
        mostrarAlert(error.message || 'Erro ao atualizar usuário', 'error');
    }
}

// Excluir usuário
async function excluirUsuario(userId, username) {
    if (!confirm(`⚠️ ATENÇÃO: Tem certeza que deseja EXCLUIR permanentemente o usuário "${username}"?\n\nEsta ação não pode ser desfeita!`)) {
        return;
    }
    
    if (!confirm(`🔴 CONFIRMAÇÃO FINAL:\n\nVocê está prestes a EXCLUIR PERMANENTEMENTE o usuário "${username}".\n\nEsta ação é IRREVERSÍVEL!\n\nDeseja realmente continuar?`)) {
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao excluir usuário');
        }
        
        mostrarAlert('Usuário excluído com sucesso!', 'success');
        carregarUsuarios();
    } catch (error) {
        console.error('Erro:', error);
        mostrarAlert(error.message || 'Erro ao excluir usuário', 'error');
    }
}

// Desativar usuário
async function desativarUsuario(userId, username) {
    if (!confirm(`⚠️ Deseja desativar o usuário "${username}"?\n\nO usuário não poderá mais fazer login, mas os dados serão preservados.`)) {
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/users/${userId}/desativar`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao desativar usuário');
        }
        
        mostrarAlert('Usuário desativado com sucesso!', 'success');
        carregarUsuarios();
    } catch (error) {
        console.error('Erro:', error);
        mostrarAlert(error.message || 'Erro ao desativar usuário', 'error');
    }
}

// Ativar usuário
async function ativarUsuario(userId) {
    try {
        const token = localStorage.getItem('access_token');
        
        // Usa a rota de atualização para ativar
        const formData = new FormData();
        formData.append('is_active', 'true');
        
        const response = await fetch(`/api/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao ativar usuário');
        }
        
        mostrarAlert('Usuário ativado com sucesso!', 'success');
        carregarUsuarios();
    } catch (error) {
        console.error('Erro:', error);
        mostrarAlert(error.message || 'Erro ao ativar usuário', 'error');
    }
}

// Garantir que funções estão disponíveis globalmente
window.excluirUsuario = excluirUsuario;
window.desativarUsuario = desativarUsuario;
window.ativarUsuario = ativarUsuario;

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
    // Tema escuro desabilitado - sempre remove
    aplicarTemaEscuro(false);
    
    // Carrega configurações sempre
    carregarConfiguracoes();
    
    // Carrega lista de clientes
    carregarClientes();
    
    // Aguarda auth.js carregar e verifica se é admin
    setTimeout(() => {
        const adminSection = document.getElementById('adminSection');
        if (!adminSection) return;
        
        // Verifica se é admin de várias formas
        let isUserAdmin = false;
        
        if (typeof isAdmin === 'function') {
            try {
                isUserAdmin = isAdmin();
            } catch (e) {
                console.warn('Erro ao verificar isAdmin:', e);
            }
        }
        
        if (typeof window.isAdmin === 'function') {
            try {
                isUserAdmin = window.isAdmin();
            } catch (e) {
                console.warn('Erro ao verificar window.isAdmin:', e);
            }
        }
        
        // Verifica no token JWT
        try {
            const token = localStorage.getItem('access_token');
            if (token) {
                const payload = JSON.parse(atob(token.split('.')[1]));
                if (payload.is_admin === true) {
                    isUserAdmin = true;
                }
            }
        } catch (e) {
            console.warn('Erro ao verificar token:', e);
        }
        
        console.log('🔍 Verificação de Admin:', isUserAdmin);
        
        if (isUserAdmin) {
            adminSection.style.display = 'block';
            carregarUsuarios();
        } else {
            adminSection.style.display = 'none';
        }
    }, 800);
    
    // Tema escuro desabilitado - não adiciona listener
});

