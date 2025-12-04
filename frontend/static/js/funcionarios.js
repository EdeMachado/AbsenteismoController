/**
 * Análise por Funcionários
 */

let funcionariosData = [];
let dadosFiltrados = [];
let ordenacaoCampo = null;
let ordenacaoDirecao = 'asc';

document.addEventListener('DOMContentLoaded', async () => {
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (!clientId) {
        mostrarMensagem('Selecione um cliente na aba "Clientes" para visualizar os funcionários.', 'aviso');
        renderizarFuncionarios([]);
        renderizarResumo([]);
        return;
    }
    await carregarFuncionarios(clientId);
    configurarPesquisa();
});

function configurarPesquisa() {
    // Configura eventos de filtro se necessário
    const filtroFuncionario = document.getElementById('filtroFuncionario');
    const filtroSetor = document.getElementById('filtroSetor');
    
    if (filtroFuncionario) {
        filtroFuncionario.addEventListener('change', () => {
            aplicarFiltrosFuncionarios();
        });
    }
    
    if (filtroSetor) {
        filtroSetor.addEventListener('change', () => {
            aplicarFiltrosFuncionarios();
        });
    }
    
    const filtroPeriodo = document.getElementById('filtroPeriodo');
    if (filtroPeriodo) {
        filtroPeriodo.addEventListener('change', () => {
            aplicarFiltrosFuncionarios();
        });
    }
    
    // Configura filtros de coluna
    document.querySelectorAll('.column-filter').forEach(filter => {
        filter.addEventListener('input', aplicarFiltrosColuna);
        filter.addEventListener('change', aplicarFiltrosColuna);
    });
}

function aplicarFiltrosColuna() {
    const rows = document.querySelectorAll('#funcionariosTableBody tr');
    const filters = {
        1: document.querySelector('.column-filter[data-column="1"]')?.value.toLowerCase() || '',
        2: document.querySelector('.column-filter[data-column="2"]')?.value.toLowerCase() || '',
        3: document.querySelector('.column-filter[data-column="3"]')?.value || ''
    };
    
    rows.forEach(row => {
        if (row.querySelector('td[colspan]')) {
            return; // Pula linha de "nenhum dado"
        }
        
        let mostrar = true;
        const cells = row.querySelectorAll('td');
        
        // Filtro por nome (coluna 1, pulando checkbox)
        if (filters[1] && cells[1]) {
            const texto = cells[1].textContent.toLowerCase();
            if (!texto.includes(filters[1])) {
                mostrar = false;
            }
        }
        
        // Filtro por setor (coluna 2)
        if (mostrar && filters[2] && cells[2]) {
            const texto = cells[2].textContent.toLowerCase();
            if (!texto.includes(filters[2])) {
                mostrar = false;
            }
        }
        
        // Filtro por gênero (coluna 3)
        if (mostrar && filters[3] && cells[3]) {
            const texto = cells[3].textContent.trim();
            const htmlContent = cells[3].innerHTML;
            
            if (filters[3] === 'vazio') {
                // Verifica se contém "Vazio" ou se é apenas "-"
                if (!htmlContent.includes('Vazio') && texto !== '-' && texto !== '') {
                    mostrar = false;
                }
            } else if (filters[3] === 'M') {
                if (!texto.includes('Masculino')) {
                    mostrar = false;
                }
            } else if (filters[3] === 'F') {
                if (!texto.includes('Feminino')) {
                    mostrar = false;
                }
            }
        }
        
        row.style.display = mostrar ? '' : 'none';
    });
    
    // Atualiza contador de seleção após aplicar filtros
    atualizarContadorSelecao();
}

function mostrarMensagem(mensagem, tipo = 'info') {
    // Cria ou atualiza mensagem na página
    let msgDiv = document.getElementById('mensagemFuncionarios');
    if (!msgDiv) {
        msgDiv = document.createElement('div');
        msgDiv.id = 'mensagemFuncionarios';
        msgDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; padding: 16px 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 1000; max-width: 400px;';
        document.body.appendChild(msgDiv);
    }
    
    const cores = {
        'erro': { bg: '#f8d7da', color: '#721c24', border: '#f5c6cb' },
        'aviso': { bg: '#fff3cd', color: '#856404', border: '#ffeaa7' },
        'info': { bg: '#d1ecf1', color: '#0c5460', border: '#bee5eb' },
        'sucesso': { bg: '#d4edda', color: '#155724', border: '#c3e6cb' }
    };
    
    const cor = cores[tipo] || cores.info;
    msgDiv.style.background = cor.bg;
    msgDiv.style.color = cor.color;
    msgDiv.style.border = `1px solid ${cor.border}`;
    msgDiv.textContent = mensagem;
    msgDiv.style.display = 'block';
    
    // Remove após 5 segundos
    setTimeout(() => {
        if (msgDiv) {
            msgDiv.style.display = 'none';
        }
    }, 5000);
}

async function carregarFuncionarios(clientIdParam) {
    try {
        const clientId = clientIdParam ?? (typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null);
        if (!clientId) {
            renderizarFuncionarios([]);
            renderizarResumo([]);
            return;
        }
        
        const response = await fetch(`/api/analises/funcionarios?client_id=${clientId}`);
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        const dados = await response.json();
        funcionariosData = dados || [];
        
        // Ordena alfabeticamente por nome (garantia extra)
        funcionariosData.sort((a, b) => {
            const nomeA = (a.nome || '').toLowerCase();
            const nomeB = (b.nome || '').toLowerCase();
            return nomeA.localeCompare(nomeB, 'pt-BR');
        });
        
        renderizarFuncionarios(funcionariosData);
        renderizarResumo(funcionariosData);
        carregarSetores(funcionariosData);
        carregarFuncionariosDropdown(funcionariosData);
    } catch (error) {
        console.error('Erro ao carregar funcionários:', error);
        mostrarMensagem('Erro ao carregar funcionários: ' + error.message, 'erro');
        renderizarFuncionarios([]);
        renderizarResumo([]);
    }
}

function aplicarOrdenacaoFuncionarios() {
    const campo = document.getElementById('ordenacaoCampo')?.value;
    const direcao = document.getElementById('ordenacaoDirecao')?.value || 'asc';
    
    ordenacaoCampo = campo;
    ordenacaoDirecao = direcao;
    
    if (!campo || dadosFiltrados.length === 0) {
        renderizarFuncionarios(dadosFiltrados);
        return;
    }
    
    // Cria uma cópia para ordenar
    const dadosOrdenados = [...dadosFiltrados];
    
    dadosOrdenados.sort((a, b) => {
        let valA, valB;
        
        switch(campo) {
            case 'nome':
                valA = (a.nome || '').toLowerCase();
                valB = (b.nome || '').toLowerCase();
                break;
            case 'setor':
                valA = (a.setor || '').toLowerCase();
                valB = (b.setor || '').toLowerCase();
                break;
            case 'genero':
                valA = (a.genero || '').toLowerCase();
                valB = (b.genero || '').toLowerCase();
                break;
            case 'total_atestados':
                valA = a.quantidade || 0;
                valB = b.quantidade || 0;
                break;
            case 'total_dias':
                valA = a.dias_perdidos || 0;
                valB = b.dias_perdidos || 0;
                break;
            case 'total_horas':
                valA = a.horas_perdidas || 0;
                valB = b.horas_perdidas || 0;
                break;
            default:
                return 0;
        }
        
        if (typeof valA === 'string' && typeof valB === 'string') {
            return direcao === 'asc' ? valA.localeCompare(valB, 'pt-BR') : valB.localeCompare(valA, 'pt-BR');
        }
        
        if (typeof valA === 'number' && typeof valB === 'number') {
            return direcao === 'asc' ? valA - valB : valB - valA;
        }
        
        return 0;
    });
    
    renderizarFuncionarios(dadosOrdenados);
}

function renderizarFuncionarios(dados) {
    const tbody = document.getElementById('funcionariosTableBody');
    
    if (!tbody) {
        console.error('Elemento funcionariosTableBody não encontrado');
        return;
    }
    
    if (!dados || dados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <i class="fas fa-inbox"></i> Nenhum funcionário encontrado
                </td>
            </tr>
        `;
        dadosFiltrados = [];
        atualizarContadorSelecao();
        return;
    }
    
    dadosFiltrados = dados;
    
    // Aplica ordenação se houver
    if (ordenacaoCampo) {
        aplicarOrdenacaoFuncionarios();
        return;
    }
    
    tbody.innerHTML = dados.map((f, index) => {
        const generoDisplay = f.genero === 'M' ? 'Masculino' : (f.genero === 'F' ? 'Feminino' : '<span style="color: var(--warning);">Vazio</span>');
        const generoClass = !f.genero ? 'editable-cell' : '';
        const nomeEscapado = (f.nome || '').replace(/'/g, "&#39;").replace(/"/g, "&quot;");
        const setorEscapado = (f.setor || '').replace(/'/g, "&#39;").replace(/"/g, "&quot;");
        const nomeEncoded = encodeURIComponent(f.nome || '');
        const nomeLimpo = f.nome || '';
        
        return `
        <tr class="funcionario-row" data-nome="${nomeEncoded}" data-index="${index}">
            <td style="text-align: center;">
                <input type="checkbox" class="checkbox-selecao" data-nome="${nomeLimpo}" onchange="atualizarContadorSelecao()">
            </td>
            <td><strong>${f.nome || 'Não informado'}</strong></td>
            <td class="editable-cell" onclick="editarFuncionario('${nomeEncoded}', 'setor', '', '${setorEscapado}')">
                ${f.setor || '-'} <i class="fas fa-edit edit-icon"></i>
            </td>
            <td class="${generoClass}" onclick="editarFuncionario('${nomeEncoded}', 'genero', '${f.genero || ''}')">
                ${generoDisplay} <i class="fas fa-edit edit-icon"></i>
            </td>
            <td style="font-weight: 600;">${f.quantidade || 0}</td>
            <td>${Math.round(f.dias_perdidos || 0)}</td>
            <td>${Math.round(f.horas_perdidas || 0).toLocaleString('pt-BR')}</td>
            <td>${getBadge(f.quantidade || 0)}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="window.location.href='/perfil_funcionario?nome=${nomeEncoded}'" title="Ver Perfil">
                    <i class="fas fa-user-circle"></i> Perfil
                </button>
                <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); editarFuncionario('${nomeEncoded}', 'todos', '${f.genero || ''}', '${setorEscapado}')" title="Editar">
                    <i class="fas fa-edit"></i> Editar
                </button>
            </td>
        </tr>
    `;
    }).join('');
    
    // Aplica filtros de coluna após renderizar
    aplicarFiltrosColuna();
    
    // Atualiza contador de seleção
    atualizarContadorSelecao();
}

function renderizarResumo(dados) {
    if (!dados || dados.length === 0) {
        const totalFuncionarios = document.getElementById('totalFuncionarios');
        const mediaAtestados = document.getElementById('mediaAtestados');
        const mediaDias = document.getElementById('mediaDias');
        
        if (totalFuncionarios) totalFuncionarios.textContent = '0';
        if (mediaAtestados) mediaAtestados.textContent = '0';
        if (mediaDias) mediaDias.textContent = '0';
        return;
    }
    
    const total = dados.length;
    const somaAtestados = dados.reduce((acc, f) => acc + (f.quantidade || 0), 0);
    const somaDias = dados.reduce((acc, f) => acc + (f.dias_perdidos || 0), 0);
    
    const mediaAtestados = total > 0 ? (somaAtestados / total).toFixed(1) : '0';
    const mediaDias = total > 0 ? (somaDias / total).toFixed(1) : '0';
    
    const totalFuncionarios = document.getElementById('totalFuncionarios');
    const mediaAtestadosEl = document.getElementById('mediaAtestados');
    const mediaDiasEl = document.getElementById('mediaDias');
    
    if (totalFuncionarios) totalFuncionarios.textContent = total;
    if (mediaAtestadosEl) mediaAtestadosEl.textContent = mediaAtestados;
    if (mediaDiasEl) mediaDiasEl.textContent = mediaDias;
}

function carregarSetores(dados) {
    const select = document.getElementById('filtroSetor');
    if (!select) return;
    
    if (!dados || dados.length === 0) {
        select.innerHTML = '<option value="">Todos</option>';
        return;
    }
    
    const setores = [...new Set(dados.map(f => f.setor).filter(s => s && s !== 'Não informado'))].sort();
    select.innerHTML = '<option value="">Todos</option>' + 
        setores.map(s => `<option value="${s}">${s}</option>`).join('');
}

function carregarFuncionariosDropdown(dados) {
    const select = document.getElementById('filtroFuncionario');
    if (!select) return;
    
    if (!dados || dados.length === 0) {
        select.innerHTML = '<option value="">Todos</option>';
        return;
    }
    
    const funcionarios = [...new Set(dados.map(f => f.nome).filter(n => n && n !== 'Não informado'))].sort();
    select.innerHTML = '<option value="">Todos</option>' + 
        funcionarios.map(f => `<option value="${f}">${f}</option>`).join('');
}

function getBadge(quantidade) {
    if (quantidade >= 5) {
        return '<span class="badge badge-high">Alto</span>';
    } else if (quantidade >= 3) {
        return '<span class="badge badge-medium">Médio</span>';
    } else {
        return '<span class="badge badge-low">Baixo</span>';
    }
}

function setupSearch() {
    // Removido - agora usa dropdown
}

function aplicarFiltrosFuncionarios() {
    const filtroFuncionario = document.getElementById('filtroFuncionario');
    const filtroSetor = document.getElementById('filtroSetor');
    const filtroPeriodo = document.getElementById('filtroPeriodo');
    
    const funcionario = filtroFuncionario ? filtroFuncionario.value : '';
    const setor = filtroSetor ? filtroSetor.value : '';
    const periodo = filtroPeriodo ? filtroPeriodo.value : '';
    
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (!clientId) {
        mostrarMensagem('Selecione um cliente para aplicar filtros de funcionários.', 'aviso');
        return;
    }
    
    let url = `/api/analises/funcionarios?client_id=${clientId}`;
    if (periodo) {
        url += `&mes_inicio=${periodo}&mes_fim=${periodo}`;
    }
    
    // Mostra loading
    const tbody = document.getElementById('funcionariosTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <i class="fas fa-spinner fa-spin"></i> Carregando...
                </td>
            </tr>
        `;
    }
    
    fetch(url)
        .then(res => {
            if (!res.ok) {
                throw new Error(`Erro ${res.status}: ${res.statusText}`);
            }
            return res.json();
        })
        .then(data => {
            funcionariosData = data || [];
            
            let filtrados = [...funcionariosData];
            
            if (funcionario) {
                filtrados = filtrados.filter(f => f.nome === funcionario);
            }
            
            if (setor) {
                filtrados = filtrados.filter(f => f.setor === setor);
            }
            
            // Ordena alfabeticamente por nome
            filtrados.sort((a, b) => {
                const nomeA = (a.nome || '').toLowerCase();
                const nomeB = (b.nome || '').toLowerCase();
                return nomeA.localeCompare(nomeB, 'pt-BR');
            });
            
            renderizarFuncionarios(filtrados);
            renderizarResumo(filtrados);
        })
        .catch(error => {
            console.error('Erro ao aplicar filtros:', error);
            mostrarMensagem('Erro ao aplicar filtros: ' + error.message, 'erro');
            renderizarFuncionarios([]);
            renderizarResumo([]);
        });
}

function exportarExcel() {
    alert('Funcionalidade de export será implementada em breve!');
}

// Funções de edição
function editarFuncionario(nome, campo, generoAtual = '', setorAtual = '') {
    const nomeDecodificado = decodeURIComponent(nome);
    document.getElementById('editNome').value = nomeDecodificado;
    
    // Decodifica HTML entities
    const setorDecodificado = setorAtual
        .replace(/&#39;/g, "'")
        .replace(/&quot;/g, '"')
        .replace(/&amp;/g, '&');
    
    if (campo === 'genero' || campo === 'todos') {
        document.getElementById('editGenero').value = generoAtual || '';
    }
    
    if (campo === 'setor' || campo === 'todos') {
        document.getElementById('editSetor').value = setorDecodificado || '';
    }
    
    const modal = document.getElementById('editModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function fecharModal() {
    const modal = document.getElementById('editModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function salvarEdicao(event) {
    event.preventDefault();
    
    const nome = document.getElementById('editNome').value;
    const genero = document.getElementById('editGenero').value;
    const setor = document.getElementById('editSetor').value;
    
    if (!nome) {
        alert('Nome do funcionário não informado');
        return;
    }
    
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (!clientId) {
        alert('Selecione um cliente para editar funcionários.');
        return;
    }
    
    try {
        // Monta URL com parâmetros
        let url = `/api/funcionario/atualizar?nome=${encodeURIComponent(nome)}&client_id=${clientId}`;
        if (genero) {
            url += `&genero=${encodeURIComponent(genero)}`;
        }
        if (setor) {
            url += `&setor=${encodeURIComponent(setor)}`;
        }
        
        const response = await fetch(url, {
            method: 'PUT'
        });
        
        if (!response.ok) {
            let errorMessage = 'Erro ao atualizar funcionário';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
            } catch (e) {
                errorMessage = `Erro ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        mostrarMensagem(result.mensagem || 'Funcionário atualizado com sucesso!', 'sucesso');
        
        // Fecha modal e recarrega dados
        fecharModal();
        
        // Recarrega a lista de funcionários
        await carregarFuncionarios(clientId);
        
    } catch (error) {
        console.error('Erro ao salvar edição:', error);
        mostrarMensagem('Erro ao atualizar funcionário: ' + error.message, 'erro');
    }
}

// Fecha modal ao clicar fora
window.onclick = function(event) {
    const modal = document.getElementById('editModal');
    if (event.target === modal) {
        fecharModal();
    }
}

// Funções de seleção em massa
function selecionarTodos(checkbox) {
    const checkboxes = document.querySelectorAll('.checkbox-selecao');
    checkboxes.forEach(cb => {
        if (cb.closest('tr').style.display !== 'none') {
            cb.checked = checkbox.checked;
        }
    });
    atualizarContadorSelecao();
}

function atualizarContadorSelecao() {
    const checkboxes = document.querySelectorAll('.checkbox-selecao:checked');
    const acoesMassa = document.getElementById('acoesMassa');
    const contador = document.getElementById('contadorSelecionados');
    
    if (checkboxes.length > 0) {
        acoesMassa.style.display = 'flex';
        contador.textContent = `${checkboxes.length} funcionário(s) selecionado(s)`;
    } else {
        acoesMassa.style.display = 'none';
    }
    
    // Atualiza checkbox "Selecionar Todos" - considera apenas linhas visíveis
    const checkboxesVisiveis = Array.from(document.querySelectorAll('.checkbox-selecao')).filter(cb => {
        const row = cb.closest('tr');
        return row && row.style.display !== 'none';
    });
    const totalVisiveis = checkboxesVisiveis.length;
    const totalSelecionados = checkboxesVisiveis.filter(cb => cb.checked).length;
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.checked = totalSelecionados > 0 && totalSelecionados === totalVisiveis;
        selectAll.indeterminate = totalSelecionados > 0 && totalSelecionados < totalVisiveis;
    }
}

function limparSelecao() {
    document.querySelectorAll('.checkbox-selecao').forEach(cb => cb.checked = false);
    const selectAll = document.getElementById('selectAll');
    if (selectAll) selectAll.checked = false;
    atualizarContadorSelecao();
}

async function aplicarGeneroMassa(genero) {
    const checkboxes = document.querySelectorAll('.checkbox-selecao:checked');
    
    if (checkboxes.length === 0) {
        alert('Selecione pelo menos um funcionário');
        return;
    }
    
    const nomes = Array.from(checkboxes).map(cb => cb.dataset.nome);
    const generoTexto = genero === 'M' ? 'Masculino' : 'Feminino';
    
    if (!confirm(`Deseja definir o gênero como ${generoTexto} para ${nomes.length} funcionário(s) selecionado(s)?\n\nIsso atualizará TODOS os registros de atestado desses funcionários.`)) {
        return;
    }
    
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (!clientId) {
        alert('Selecione um cliente para realizar a atualização em massa.');
        return;
    }
    
    try {
        // Monta URL com parâmetros
        let url = `/api/funcionarios/atualizar-massa?client_id=${clientId}&genero=${genero}`;
        nomes.forEach(nome => {
            url += `&nomes=${encodeURIComponent(nome)}`;
        });
        
        const response = await fetch(url, {
            method: 'PUT'
        });
        
        if (!response.ok) {
            let errorMessage = 'Erro ao atualizar funcionários';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
            } catch (e) {
                errorMessage = `Erro ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        mostrarMensagem(result.mensagem || 'Funcionários atualizados com sucesso!', 'sucesso');
        
        // Limpa seleção e recarrega dados
        limparSelecao();
        await carregarFuncionarios(clientId);
        
    } catch (error) {
        console.error('Erro ao aplicar gênero em massa:', error);
        mostrarMensagem('Erro ao atualizar funcionários: ' + error.message, 'erro');
    }
}
