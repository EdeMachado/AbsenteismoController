// ==================== VARIÁVEIS GLOBAIS ====================
let clientes = [];
let clienteEditando = null;

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    carregarClientes();
    
    // Fecha modal ao clicar fora
    document.getElementById('modalCliente').addEventListener('click', (e) => {
        if (e.target.id === 'modalCliente') {
            fecharModal();
        }
    });
});

// ==================== CARREGAR CLIENTES ====================
async function carregarClientes() {
    try {
        const response = await fetch('/api/clientes');
        if (!response.ok) throw new Error('Erro ao carregar clientes');
        
        clientes = await response.json();
        renderizarTabela();
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
        mostrarErro('Erro ao carregar clientes: ' + error.message);
    }
}

// ==================== RENDERIZAR TABELA ====================
function renderizarTabela() {
    const container = document.getElementById('clientesTableContainer');
    
    if (clientes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-building"></i>
                <h3>Nenhum cliente cadastrado</h3>
                <p>Clique em "Novo Cliente" para começar</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="clientes-table">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Razão Social</th>
                        <th>CNPJ</th>
                        <th>Nome Fantasia</th>
                        <th>Cidade/Estado</th>
                        <th>Telefone</th>
                        <th>E-mail</th>
                        <th>Uploads</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    ${clientes.map(c => `
                        <tr>
                            <td>${c.id}</td>
                            <td><strong>${c.nome}</strong></td>
                            <td>${formatarCNPJExibicao(c.cnpj)}</td>
                            <td>${c.nome_fantasia || '-'}</td>
                            <td>${c.cidade || '-'}${c.estado ? '/' + c.estado : ''}</td>
                            <td>${c.telefone || '-'}</td>
                            <td>${c.email || '-'}</td>
                            <td>${c.total_uploads || 0}</td>
                            <td class="acoes-cell">
                                <button class="btn-icon-small btn-edit" onclick="editarCliente(${c.id})" title="Editar">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn-icon-small btn-delete" onclick="confirmarDeletar(${c.id})" title="Deletar" ${c.total_uploads > 0 ? 'disabled style="opacity:0.5;cursor:not-allowed;"' : ''}>
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ==================== MODAL ====================
function abrirModalNovo() {
    clienteEditando = null;
    document.getElementById('modalTitle').textContent = 'Novo Cliente';
    document.getElementById('formCliente').reset();
    document.getElementById('clienteId').value = '';
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
    
    // Carrega dados completos do cliente
    carregarDadosCliente(id);
}

async function carregarDadosCliente(id) {
    try {
        const response = await fetch(`/api/clientes/${id}`);
        if (!response.ok) throw new Error('Erro ao carregar dados do cliente');
        
        const cliente = await response.json();
        
        // Preenche formulário
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
    
    // Desabilita botão e mostra loading
    btnBuscar.disabled = true;
    btnBuscar.innerHTML = '<span class="loading-spinner"></span> Buscando...';
    
    try {
        const response = await fetch(`/api/buscar-cnpj/${cnpj}`);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao buscar CNPJ');
        }
        
        const dados = await response.json();
        
        // Preenche formulário com dados retornados
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
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao salvar cliente');
        }
        
        const resultado = await response.json();
        mostrarSucesso(resultado.message || 'Cliente salvo com sucesso!');
        fecharModal();
        carregarClientes();
        
    } catch (error) {
        console.error('Erro ao salvar cliente:', error);
        mostrarErro('Erro ao salvar cliente: ' + error.message);
    }
}

// ==================== DELETAR CLIENTE ====================
async function confirmarDeletar(id) {
    if (!confirm('Tem certeza que deseja deletar este cliente?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/clientes/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao deletar cliente');
        }
        
        mostrarSucesso('Cliente deletado com sucesso!');
        carregarClientes();
        
    } catch (error) {
        console.error('Erro ao deletar cliente:', error);
        mostrarErro('Erro ao deletar cliente: ' + error.message);
        alert(error.message);
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
    // Converte de DD/MM/YYYY para YYYY-MM-DD
    if (data.includes('/')) {
        const [dia, mes, ano] = data.split('/');
        return `${ano}-${mes}-${dia}`;
    }
    return data;
}

// ==================== UTILITÁRIOS ====================
function mostrarSucesso(mensagem) {
    // Você pode implementar um toast notification aqui
    alert(mensagem);
}

function mostrarErro(mensagem) {
    alert('Erro: ' + mensagem);
}

