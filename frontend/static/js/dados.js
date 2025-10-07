/**
 * Dados JavaScript - AbsenteismoController v2.0
 * Gestão completa de dados: visualização, edição, adição, exclusão
 */

let dadosCompletos = [];
let dadosFiltrados = [];
let paginaAtual = 1;
const registrosPorPagina = 50;
let uploadSelecionado = null;
let modoEdicao = false;

// Inicializa a página
document.addEventListener('DOMContentLoaded', () => {
    carregarUploads();
    carregarDados();
});

// Carrega lista de uploads para o filtro
async function carregarUploads() {
    try {
        const response = await fetch('/api/uploads?client_id=1');
        const uploads = await response.json();
        
        const select = document.getElementById('filtroUpload');
        select.innerHTML = '<option value="">Todos os uploads</option>' +
            uploads.map(u => `<option value="${u.id}">${u.filename} - ${formatMesReferencia(u.mes_referencia)}</option>`).join('');
        
        // Se houver upload_id na URL, seleciona automaticamente
        const urlParams = new URLSearchParams(window.location.search);
        const uploadId = urlParams.get('upload_id');
        if (uploadId) {
            select.value = uploadId;
        }
        
    } catch (error) {
        console.error('Erro ao carregar uploads:', error);
    }
}

// Carrega todos os dados
async function carregarDados() {
    try {
        const uploadId = document.getElementById('filtroUpload').value;
        
        let url = '/api/dados/todos?client_id=1';
        if (uploadId) {
            url += `&upload_id=${uploadId}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        dadosCompletos = data.dados || [];
        dadosFiltrados = [...dadosCompletos];
        
        atualizarEstatisticas(data.estatisticas);
        renderizarTabela();
        
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        document.getElementById('dadosTableBody').innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; color: var(--danger); padding: 40px;">
                    Erro ao carregar dados. Tente novamente.
                </td>
            </tr>
        `;
    }
}

// Atualiza estatísticas no topo
function atualizarEstatisticas(stats) {
    document.getElementById('totalRegistros').textContent = stats.total_registros.toLocaleString('pt-BR');
    document.getElementById('totalDias').textContent = stats.total_atestados_dias.toLocaleString('pt-BR');
    document.getElementById('totalHoras').textContent = stats.total_atestados_horas.toLocaleString('pt-BR');
    document.getElementById('diasPerdidos').textContent = Math.round(stats.total_dias_perdidos).toLocaleString('pt-BR');
}

// Renderiza a tabela com paginação
function renderizarTabela() {
    const inicio = (paginaAtual - 1) * registrosPorPagina;
    const fim = inicio + registrosPorPagina;
    const dadosPagina = dadosFiltrados.slice(inicio, fim);
    
    const tbody = document.getElementById('dadosTableBody');
    
    if (dadosPagina.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; color: var(--text-secondary); padding: 40px;">
                    Nenhum registro encontrado.
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = dadosPagina.map(d => `
        <tr>
            <td><strong>${d.nome_funcionario || '-'}</strong></td>
            <td>${formatCPF(d.cpf)}</td>
            <td>${d.setor || '-'}</td>
            <td>${formatData(d.data_afastamento)}</td>
            <td>
                <span class="badge ${d.tipo_info_atestado === 1 ? 'badge-dias' : 'badge-horas'}">
                    ${d.tipo_info_atestado === 1 ? 'Dias' : 'Horas'}
                </span>
            </td>
            <td>
                <strong>${d.cid || '-'}</strong><br>
                <small style="color: var(--text-secondary);">${truncate(d.descricao_cid || '', 40)}</small>
            </td>
            <td>
                ${d.tipo_info_atestado === 1 
                    ? `<strong>${d.numero_dias_atestado || 0}</strong> dias` 
                    : `<strong>${d.numero_horas_atestado || 0}</strong> horas`
                }
            </td>
            <td>
                <div class="action-btns">
                    <button class="btn-icon-small" onclick="editarRegistro(${d.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon-small delete" onclick="excluirRegistro(${d.id})" title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    atualizarPaginacao();
}

// Atualiza controles de paginação
function atualizarPaginacao() {
    const totalPaginas = Math.ceil(dadosFiltrados.length / registrosPorPagina);
    const inicio = (paginaAtual - 1) * registrosPorPagina + 1;
    const fim = Math.min(paginaAtual * registrosPorPagina, dadosFiltrados.length);
    
    document.getElementById('paginationInfo').textContent = 
        `Mostrando ${inicio} a ${fim} de ${dadosFiltrados.length} registros`;
    
    document.getElementById('btnAnterior').disabled = paginaAtual === 1;
    document.getElementById('btnProxima').disabled = paginaAtual === totalPaginas || totalPaginas === 0;
    
    // Renderiza botões de páginas
    let pagesHtml = '';
    const maxPages = 5;
    let startPage = Math.max(1, paginaAtual - Math.floor(maxPages / 2));
    let endPage = Math.min(totalPaginas, startPage + maxPages - 1);
    
    if (endPage - startPage < maxPages - 1) {
        startPage = Math.max(1, endPage - maxPages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        pagesHtml += `
            <button class="pagination-btn ${i === paginaAtual ? 'active' : ''}" onclick="irParaPagina(${i})">
                ${i}
            </button>
        `;
    }
    
    document.getElementById('paginationPages').innerHTML = pagesHtml;
}

// Navegação de páginas
function mudarPagina(direcao) {
    const totalPaginas = Math.ceil(dadosFiltrados.length / registrosPorPagina);
    paginaAtual = Math.max(1, Math.min(totalPaginas, paginaAtual + direcao));
    renderizarTabela();
}

function irParaPagina(pagina) {
    paginaAtual = pagina;
    renderizarTabela();
}

// Busca em tempo real
function buscarDados() {
    const termo = document.getElementById('searchInput').value.toLowerCase();
    
    if (!termo) {
        dadosFiltrados = [...dadosCompletos];
    } else {
        dadosFiltrados = dadosCompletos.filter(d => {
            return (
                (d.nome_funcionario || '').toLowerCase().includes(termo) ||
                (d.cpf || '').toLowerCase().includes(termo) ||
                (d.setor || '').toLowerCase().includes(termo) ||
                (d.cid || '').toLowerCase().includes(termo) ||
                (d.descricao_cid || '').toLowerCase().includes(termo)
            );
        });
    }
    
    paginaAtual = 1;
    renderizarTabela();
}

// Filtro por tipo
function filtrarPorTipo() {
    const tipo = document.getElementById('filtroTipo').value;
    const termo = document.getElementById('searchInput').value.toLowerCase();
    
    // Aplica filtro de busca primeiro
    let dados = dadosCompletos;
    if (termo) {
        dados = dados.filter(d => {
            return (
                (d.nome_funcionario || '').toLowerCase().includes(termo) ||
                (d.cpf || '').toLowerCase().includes(termo) ||
                (d.setor || '').toLowerCase().includes(termo) ||
                (d.cid || '').toLowerCase().includes(termo) ||
                (d.descricao_cid || '').toLowerCase().includes(termo)
            );
        });
    }
    
    // Aplica filtro de tipo
    if (tipo) {
        dadosFiltrados = dados.filter(d => d.tipo_info_atestado === parseInt(tipo));
    } else {
        dadosFiltrados = dados;
    }
    
    paginaAtual = 1;
    renderizarTabela();
}

// Modal - Abrir para novo registro
function abrirModalNovo() {
    modoEdicao = false;
    document.getElementById('modalTitle').textContent = 'Novo Registro';
    document.getElementById('formRegistro').reset();
    document.getElementById('registroId').value = '';
    
    // Pega o upload_id atual se houver filtro
    const uploadId = document.getElementById('filtroUpload').value;
    if (uploadId) {
        document.getElementById('uploadId').value = uploadId;
    }
    
    document.getElementById('modalRegistro').classList.add('active');
}

// Modal - Abrir para editar registro
async function editarRegistro(id) {
    modoEdicao = true;
    document.getElementById('modalTitle').textContent = 'Editar Registro';
    
    try {
        const response = await fetch(`/api/dados/${id}`);
        const registro = await response.json();
        
        // Preenche o formulário
        document.getElementById('registroId').value = registro.id;
        document.getElementById('uploadId').value = registro.upload_id;
        document.getElementById('nomeFuncionario').value = registro.nome_funcionario || '';
        document.getElementById('cpf').value = registro.cpf || '';
        document.getElementById('matricula').value = registro.matricula || '';
        document.getElementById('setor').value = registro.setor || '';
        document.getElementById('cargo').value = registro.cargo || '';
        document.getElementById('genero').value = registro.genero || '';
        document.getElementById('dataAfastamento').value = registro.data_afastamento || '';
        document.getElementById('dataRetorno').value = registro.data_retorno || '';
        document.getElementById('tipoInfoAtestado').value = registro.tipo_info_atestado || '';
        document.getElementById('numeroDias').value = registro.numero_dias_atestado || '';
        document.getElementById('numeroHoras').value = registro.numero_horas_atestado || '';
        document.getElementById('cid').value = registro.cid || '';
        document.getElementById('descricaoCid').value = registro.descricao_cid || '';
        
        mudarTipoAtestado();
        
        document.getElementById('modalRegistro').classList.add('active');
        
    } catch (error) {
        console.error('Erro ao carregar registro:', error);
        alert('Erro ao carregar dados do registro');
    }
}

// Modal - Fechar
function fecharModal() {
    document.getElementById('modalRegistro').classList.remove('active');
    document.getElementById('formRegistro').reset();
}

// Modal - Mudar tipo de atestado (Dias/Horas)
function mudarTipoAtestado() {
    const tipo = document.getElementById('tipoInfoAtestado').value;
    
    if (tipo === '1') {
        document.getElementById('fieldNumeroDias').style.display = 'block';
        document.getElementById('fieldNumeroHoras').style.display = 'none';
        document.getElementById('numeroHoras').value = '';
    } else if (tipo === '3') {
        document.getElementById('fieldNumeroDias').style.display = 'none';
        document.getElementById('fieldNumeroHoras').style.display = 'block';
        document.getElementById('numeroDias').value = '';
    } else {
        document.getElementById('fieldNumeroDias').style.display = 'none';
        document.getElementById('fieldNumeroHoras').style.display = 'none';
    }
}

// Salvar registro (novo ou editado)
async function salvarRegistro() {
    const form = document.getElementById('formRegistro');
    if (!form.checkValidity()) {
        alert('Preencha todos os campos obrigatórios (*)');
        return;
    }
    
    const id = document.getElementById('registroId').value;
    const uploadId = document.getElementById('uploadId').value;
    
    if (!modoEdicao && !uploadId) {
        alert('Selecione um upload antes de adicionar um novo registro');
        return;
    }
    
    const dados = {
        upload_id: parseInt(uploadId) || null,
        nome_funcionario: document.getElementById('nomeFuncionario').value,
        cpf: document.getElementById('cpf').value,
        matricula: document.getElementById('matricula').value,
        setor: document.getElementById('setor').value,
        cargo: document.getElementById('cargo').value,
        genero: document.getElementById('genero').value,
        data_afastamento: document.getElementById('dataAfastamento').value,
        data_retorno: document.getElementById('dataRetorno').value,
        tipo_info_atestado: parseInt(document.getElementById('tipoInfoAtestado').value),
        numero_dias_atestado: parseFloat(document.getElementById('numeroDias').value) || 0,
        numero_horas_atestado: parseFloat(document.getElementById('numeroHoras').value) || 0,
        cid: document.getElementById('cid').value,
        descricao_cid: document.getElementById('descricaoCid').value
    };
    
    // Calcula horas e dias perdidos
    if (dados.tipo_info_atestado === 1) {
        dados.dias_perdidos = dados.numero_dias_atestado;
        dados.horas_perdidas = dados.numero_dias_atestado * 8;
    } else {
        dados.dias_perdidos = 0;
        dados.horas_perdidas = dados.numero_horas_atestado;
    }
    
    try {
        let response;
        if (modoEdicao) {
            // Atualizar registro existente
            response = await fetch(`/api/dados/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });
        } else {
            // Criar novo registro
            response = await fetch('/api/dados', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });
        }
        
        if (response.ok) {
            alert(modoEdicao ? 'Registro atualizado com sucesso!' : 'Registro criado com sucesso!');
            fecharModal();
            carregarDados();
        } else {
            const error = await response.json();
            alert('Erro ao salvar: ' + (error.detail || 'Erro desconhecido'));
        }
        
    } catch (error) {
        console.error('Erro ao salvar registro:', error);
        alert('Erro ao salvar registro');
    }
}

// Excluir registro
async function excluirRegistro(id) {
    if (!confirm('Tem certeza que deseja excluir este registro? Esta ação não pode ser desfeita.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/dados/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Registro excluído com sucesso!');
            carregarDados();
        } else {
            alert('Erro ao excluir registro');
        }
        
    } catch (error) {
        console.error('Erro ao excluir registro:', error);
        alert('Erro ao excluir registro');
    }
}

// Exportar dados para Excel
async function exportarDados() {
    try {
        const uploadId = document.getElementById('filtroUpload').value;
        let url = '/api/export/excel?client_id=1';
        if (uploadId) {
            url += `&upload_id=${uploadId}`;
        }
        
        window.location.href = url;
        
    } catch (error) {
        console.error('Erro ao exportar:', error);
        alert('Erro ao exportar dados');
    }
}

// Utilities
function formatCPF(cpf) {
    if (!cpf) return '-';
    cpf = cpf.replace(/\D/g, '');
    if (cpf.length === 11) {
        return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
    return cpf;
}

function formatData(dataStr) {
    if (!dataStr) return '-';
    const date = new Date(dataStr);
    return date.toLocaleDateString('pt-BR');
}

function formatMesReferencia(mes) {
    if (!mes) return '-';
    const [ano, mesNum] = mes.split('-');
    const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    return `${meses[parseInt(mesNum) - 1]}/${ano}`;
}

function truncate(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
}

