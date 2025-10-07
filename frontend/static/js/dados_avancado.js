/**
 * Análise Avançada com IA - AbsenteismoController v2.0
 * Features: Filtros por coluna, IA para criar colunas, scroll horizontal, gerenciamento de colunas
 */

let dadosCompletos = [];
let dadosFiltrados = [];
let paginaAtual = 1;
let registrosPorPagina = 100; // Agora é variável
let mostrarTodos = false;

// Configuração de colunas
let colunasConfig = {
    // Colunas padrão da planilha
    id: { visible: false, label: 'ID', type: 'number', sticky: false },
    nome_funcionario: { visible: true, label: 'Funcionário', type: 'text', sticky: true },
    cpf: { visible: true, label: 'CPF', type: 'text', sticky: false },
    matricula: { visible: true, label: 'Matrícula', type: 'text', sticky: false },
    setor: { visible: true, label: 'Setor', type: 'text', sticky: false },
    cargo: { visible: true, label: 'Cargo', type: 'text', sticky: false },
    genero: { visible: true, label: 'Gênero', type: 'text', sticky: false },
    data_afastamento: { visible: true, label: 'Data Afastamento', type: 'date', sticky: false },
    data_retorno: { visible: true, label: 'Data Retorno', type: 'date', sticky: false },
    tipo_info_atestado: { visible: true, label: 'Tipo', type: 'number', sticky: false },
    tipo_atestado: { visible: true, label: 'Tipo Atestado', type: 'text', sticky: false },
    cid: { visible: true, label: 'CID', type: 'text', sticky: false },
    descricao_cid: { visible: true, label: 'Descrição CID', type: 'text', sticky: false },
    numero_dias_atestado: { visible: true, label: 'Nº Dias', type: 'number', sticky: false },
    numero_horas_atestado: { visible: true, label: 'Nº Horas', type: 'number', sticky: false },
    dias_perdidos: { visible: true, label: 'Dias Perdidos', type: 'number', sticky: false },
    horas_perdidas: { visible: true, label: 'Horas Perdidas', type: 'number', sticky: false },
    upload_id: { visible: false, label: 'Upload ID', type: 'number', sticky: false }
};

// Colunas criadas por IA
let colunasIA = {};

// Filtros ativos por coluna
let filtrosAtivos = {};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    carregarUploads();
    carregarDados();
    renderizarGerenciadorColunas();
});

// Carrega lista de uploads
async function carregarUploads() {
    try {
        const response = await fetch('/api/uploads?client_id=1');
        const uploads = await response.json();
        
        const select = document.getElementById('filtroUpload');
        select.innerHTML = '<option value="">Todos os uploads</option>' +
            uploads.map(u => `<option value="${u.id}">${u.filename} - ${formatMesReferencia(u.mes_referencia)}</option>`).join('');
        
        const urlParams = new URLSearchParams(window.location.search);
        const uploadId = urlParams.get('upload_id');
        if (uploadId) select.value = uploadId;
        
    } catch (error) {
        console.error('Erro ao carregar uploads:', error);
    }
}

// Carrega todos os dados
async function carregarDados() {
    try {
        const uploadId = document.getElementById('filtroUpload').value;
        let url = '/api/dados/todos?client_id=1';
        if (uploadId) url += `&upload_id=${uploadId}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        dadosCompletos = data.dados || [];
        dadosFiltrados = [...dadosCompletos];
        
        atualizarEstatisticas(data.estatisticas);
        renderizarTabela();
        
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
    }
}

function recarregarDados() {
    carregarDados();
}

// Atualiza estatísticas
function atualizarEstatisticas(stats) {
    document.getElementById('totalRegistros').textContent = stats.total_registros.toLocaleString('pt-BR');
    
    const colunasVisiveis = Object.values(colunasConfig).filter(c => c.visible).length + 
                            Object.values(colunasIA).filter(c => c.visible).length;
    document.getElementById('totalColunas').textContent = colunasVisiveis;
    
    const totalFiltros = Object.keys(filtrosAtivos).length;
    document.getElementById('totalFiltros').textContent = totalFiltros;
}

// Renderiza a tabela
function renderizarTabela() {
    const inicio = (paginaAtual - 1) * registrosPorPagina;
    const fim = inicio + registrosPorPagina;
    const dadosPagina = dadosFiltrados.slice(inicio, fim);
    
    // Cabeçalho
    const thead = document.getElementById('tableHead');
    const colunasVisiveis = Object.entries({...colunasConfig, ...colunasIA})
        .filter(([key, config]) => config.visible);
    
    thead.innerHTML = `
        <tr>
            ${colunasVisiveis.map(([key, config]) => `
                <th class="${config.sticky ? 'sticky-col' : ''}">
                    ${config.label}
                    ${config.ia ? '<span class="ia-badge">IA</span>' : ''}
                    <span class="column-filter">
                        <i class="fas fa-filter filter-icon ${filtrosAtivos[key] ? 'active' : ''}" 
                           onclick="toggleFiltroColuna(event, '${key}')"></i>
                        <div class="filter-dropdown" id="filter-${key}">
                            <input type="text" class="filter-search" placeholder="Buscar..." 
                                   onkeyup="filtrarOpcoesColuna('${key}', this.value)">
                            <div id="filter-options-${key}">
                                <!-- Será preenchido dinamicamente -->
                            </div>
                        </div>
                    </span>
                </th>
            `).join('')}
            <th style="min-width: 100px;">Ações</th>
        </tr>
    `;
    
    // Corpo
    const tbody = document.getElementById('tableBody');
    
    if (dadosPagina.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="${colunasVisiveis.length + 1}" style="text-align: center; padding: 40px;">
                    Nenhum registro encontrado
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = dadosPagina.map(registro => `
        <tr>
            ${colunasVisiveis.map(([key, config]) => {
                let valor = registro[key];
                
                // Formatação de valores
                if (config.type === 'date' && valor) {
                    valor = formatData(valor);
                } else if (config.type === 'number' && valor !== null && valor !== undefined) {
                    valor = parseFloat(valor).toLocaleString('pt-BR');
                } else if (key === 'cpf' && valor) {
                    valor = formatCPF(valor);
                } else if (key === 'tipo_info_atestado') {
                    valor = valor === 1 ? '<span class="badge badge-dias">Dias</span>' : 
                            valor === 3 ? '<span class="badge badge-horas">Horas</span>' : '-';
                } else if (valor === null || valor === undefined || valor === '') {
                    valor = '-';
                }
                
                return `<td class="${config.sticky ? 'sticky-col' : ''}">${valor}</td>`;
            }).join('')}
            <td>
                <a href="/dados?edit=${registro.id}" class="btn-icon-small" title="Editar">
                    <i class="fas fa-edit"></i>
                </a>
            </td>
        </tr>
    `).join('');
    
    atualizarPaginacao();
    preencherOpcoesFiltr os();
}

// Toggle filtro de coluna
function toggleFiltroColuna(event, coluna) {
    event.stopPropagation();
    
    const dropdown = document.getElementById(`filter-${coluna}`);
    const allDropdowns = document.querySelectorAll('.filter-dropdown');
    
    // Fecha todos os outros
    allDropdowns.forEach(d => {
        if (d.id !== `filter-${coluna}`) {
            d.classList.remove('active');
        }
    });
    
    dropdown.classList.toggle('active');
    
    if (dropdown.classList.contains('active')) {
        preencherOpcoesColuna(coluna);
    }
}

// Preenche opções de filtro de uma coluna
function preencherOpcoesColuna(coluna) {
    const container = document.getElementById(`filter-options-${coluna}`);
    
    // Pega valores únicos
    const valoresUnicos = [...new Set(dadosCompletos.map(d => {
        let val = d[coluna];
        if (val === null || val === undefined || val === '') return '(Vazio)';
        if (typeof val === 'object' && val.toISOString) {
            return formatData(val.toISOString());
        }
        return String(val);
    }))].sort();
    
    const filtrosAtuais = filtrosAtivos[coluna] || [];
    
    container.innerHTML = `
        <div class="filter-option" onclick="selecionarTodosFiltro('${coluna}', true)">
            <input type="checkbox" ${filtrosAtuais.length === 0 ? 'checked' : ''}>
            <span><strong>(Selecionar Todos)</strong></span>
        </div>
        ${valoresUnicos.map(valor => `
            <div class="filter-option" onclick="toggleFiltroOpcao('${coluna}', '${valor.replace(/'/g, "\\'")}')">
                <input type="checkbox" ${filtrosAtuais.length === 0 || filtrosAtuais.includes(valor) ? 'checked' : ''}>
                <span>${valor}</span>
            </div>
        `).join('')}
    `;
}

// Preenche opções de TODOS os filtros (chamado após renderizar tabela)
function preencherOpcoesF iltros() {
    const colunasVisiveis = Object.keys({...colunasConfig, ...colunasIA})
        .filter(key => colunasConfig[key]?.visible || colunasIA[key]?.visible);
    
    colunasVisiveis.forEach(coluna => {
        const container = document.getElementById(`filter-options-${coluna}`);
        if (container && container.innerHTML.trim() === '') {
            preencherOpcoesColuna(coluna);
        }
    });
}

// Toggle opção de filtro
function toggleFiltroOpcao(coluna, valor) {
    event.stopPropagation();
    
    if (!filtrosAtivos[coluna]) {
        filtrosAtivos[coluna] = [];
    }
    
    const index = filtrosAtivos[coluna].indexOf(valor);
    if (index > -1) {
        filtrosAtivos[coluna].splice(index, 1);
    } else {
        filtrosAtivos[coluna].push(valor);
    }
    
    // Se ficou vazio, remove o filtro
    if (filtrosAtivos[coluna].length === 0) {
        delete filtrosAtivos[coluna];
    }
    
    aplicarFiltros();
}

// Selecionar todos os filtros de uma coluna
function selecionarTodosFiltro(coluna, selecionar) {
    event.stopPropagation();
    
    if (selecionar) {
        delete filtrosAtivos[coluna];
    } else {
        filtrosAtivos[coluna] = [];
    }
    
    aplicarFiltros();
}

// Aplicar todos os filtros
function aplicarFiltros() {
    dadosFiltrados = dadosCompletos.filter(registro => {
        // Verifica cada filtro ativo
        for (let [coluna, valoresFiltro] of Object.entries(filtrosAtivos)) {
            if (valoresFiltro.length === 0) continue;
            
            let valorRegistro = registro[coluna];
            if (valorRegistro === null || valorRegistro === undefined || valorRegistro === '') {
                valorRegistro = '(Vazio)';
            } else if (typeof valorRegistro === 'object' && valorRegistro.toISOString) {
                valorRegistro = formatData(valorRegistro.toISOString());
            } else {
                valorRegistro = String(valorRegistro);
            }
            
            if (!valoresFiltro.includes(valorRegistro)) {
                return false;
            }
        }
        
        return true;
    });
    
    paginaAtual = 1;
    renderizarTabela();
}

// Limpar todos os filtros
function limparFiltros() {
    filtrosAtivos = {};
    document.getElementById('searchGlobal').value = '';
    dadosFiltrados = [...dadosCompletos];
    renderizarTabela();
}

// Busca global
function buscarGlobal() {
    const termo = document.getElementById('searchGlobal').value.toLowerCase();
    
    if (!termo) {
        dadosFiltrados = [...dadosCompletos];
    } else {
        dadosFiltrados = dadosCompletos.filter(registro => {
            return Object.values(registro).some(valor => {
                if (valor === null || valor === undefined) return false;
                return String(valor).toLowerCase().includes(termo);
            });
        });
    }
    
    paginaAtual = 1;
    renderizarTabela();
}

// Paginação
function atualizarPaginacao() {
    const totalPaginas = Math.ceil(dadosFiltrados.length / registrosPorPagina);
    const inicio = (paginaAtual - 1) * registrosPorPagina + 1;
    const fim = Math.min(paginaAtual * registrosPorPagina, dadosFiltrados.length);
    
    document.getElementById('paginationInfo').textContent = 
        `Mostrando ${inicio} a ${fim} de ${dadosFiltrados.length} registros`;
    
    document.getElementById('btnAnterior').disabled = paginaAtual === 1;
    document.getElementById('btnProxima').disabled = paginaAtual === totalPaginas || totalPaginas === 0;
    
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

function mudarPagina(direcao) {
    const totalPaginas = Math.ceil(dadosFiltrados.length / registrosPorPagina);
    paginaAtual = Math.max(1, Math.min(totalPaginas, paginaAtual + direcao));
    renderizarTabela();
}

function irParaPagina(pagina) {
    paginaAtual = pagina;
    renderizarTabela();
}

// ============ GERENCIADOR DE COLUNAS ============

function toggleColumnManager() {
    const manager = document.getElementById('columnManager');
    const overlay = document.getElementById('overlay');
    
    manager.classList.toggle('active');
    overlay.classList.toggle('active');
}

function renderizarGerenciadorColunas() {
    const container = document.getElementById('columnList');
    
    const todasColunas = {...colunasConfig, ...colunasIA};
    
    container.innerHTML = Object.entries(todasColunas).map(([key, config]) => `
        <div class="column-item">
            <input type="checkbox" ${config.visible ? 'checked' : ''} 
                   onchange="toggleColunaVisibilidade('${key}')">
            <div class="column-item-label">${config.label}</div>
            <div class="column-item-type">${config.type}</div>
            ${config.ia ? '<span class="ia-badge">IA</span>' : ''}
        </div>
    `).join('');
}

function toggleColunaVisibilidade(coluna) {
    if (colunasConfig[coluna]) {
        colunasConfig[coluna].visible = !colunasConfig[coluna].visible;
    } else if (colunasIA[coluna]) {
        colunasIA[coluna].visible = !colunasIA[coluna].visible;
    }
    
    renderizarTabela();
    renderizarGerenciadorColunas();
    atualizarEstatisticas({ total_registros: dadosCompletos.length });
}

// ============ IA PARA CRIAR COLUNAS ============

async function criarColunaIA(tipo) {
    let novaColuna = {};
    
    switch (tipo) {
        case 'genero':
            novaColuna = await criarColunaGenero();
            break;
        case 'categoria_cid':
            novaColuna = await criarColunaCategoriaCID();
            break;
        case 'duracao_afastamento':
            novaColuna = await criarColunaDuracaoAfastamento();
            break;
        case 'mes_ano':
            novaColuna = await criarColunaMesAno();
            break;
        case 'faixa_etaria':
            alert('Para criar faixa etária, precisamos do campo data de nascimento na planilha.');
            return;
    }
    
    if (novaColuna.key) {
        colunasIA[novaColuna.key] = {
            visible: true,
            label: novaColuna.label,
            type: novaColuna.type,
            sticky: false,
            ia: true
        };
        
        // Adiciona a coluna em todos os registros
        dadosCompletos.forEach((registro, index) => {
            registro[novaColuna.key] = novaColuna.calcular(registro);
        });
        
        dadosFiltrados = [...dadosCompletos];
        
        renderizarTabela();
        renderizarGerenciadorColunas();
        
        alert(`✅ Coluna "${novaColuna.label}" criada com sucesso!`);
    }
}

// Criar coluna de gênero baseado no nome - REGRA MELHORADA
async function criarColunaGenero() {
    return {
        key: 'ia_genero',
        label: 'Gênero (IA)',
        type: 'text',
        calcular: (registro) => {
            const nome = registro.nome_funcionario || '';
            if (!nome) return 'Indefinido';
            
            // Pega apenas o PRIMEIRO NOME
            const primeiroNome = nome.trim().split(' ')[0].toUpperCase();
            
            if (!primeiroNome) return 'Indefinido';
            
            // REGRA PRINCIPAL: Termina com "A" = Feminino, resto = Masculino
            const ultimaLetra = primeiroNome.charAt(primeiroNome.length - 1);
            
            if (ultimaLetra === 'A') {
                return 'F';
            } else {
                return 'M';
            }
        }
    };
}

// Criar coluna de categoria do CID
async function criarColunaCategoriaCID() {
    const categoriasCID = {
        'A': 'Infecciosas',
        'B': 'Infecciosas',
        'C': 'Neoplasias',
        'D': 'Sangue/Imunológicas',
        'E': 'Endócrinas/Metabólicas',
        'F': 'Mentais/Comportamentais',
        'G': 'Nervoso',
        'H': 'Olhos/Ouvidos',
        'I': 'Circulatórias',
        'J': 'Respiratórias',
        'K': 'Digestivas',
        'L': 'Pele',
        'M': 'Musculoesqueléticas',
        'N': 'Geniturinárias',
        'O': 'Gravidez/Parto',
        'P': 'Perinatais',
        'Q': 'Congênitas',
        'R': 'Sintomas/Sinais',
        'S': 'Traumatismos',
        'T': 'Envenenamentos',
        'V': 'Causas Externas',
        'W': 'Causas Externas',
        'X': 'Causas Externas',
        'Y': 'Causas Externas',
        'Z': 'Saúde/Exames'
    };
    
    return {
        key: 'ia_categoria_cid',
        label: 'Categoria CID (IA)',
        type: 'text',
        calcular: (registro) => {
            const cid = registro.cid || '';
            if (!cid) return '-';
            
            const letra = cid.charAt(0).toUpperCase();
            return categoriasCID[letra] || 'Outros';
        }
    };
}

// Criar coluna de duração do afastamento
async function criarColunaDuracaoAfastamento() {
    return {
        key: 'ia_duracao_dias',
        label: 'Duração (dias)',
        type: 'number',
        calcular: (registro) => {
            if (registro.tipo_info_atestado === 1) {
                return registro.numero_dias_atestado || 0;
            } else if (registro.tipo_info_atestado === 3) {
                return Math.round((registro.numero_horas_atestado || 0) / 8 * 10) / 10;
            }
            return 0;
        }
    };
}

// Criar coluna de mês/ano
async function criarColunaMesAno() {
    return {
        key: 'ia_mes_ano',
        label: 'Mês/Ano',
        type: 'text',
        calcular: (registro) => {
            if (!registro.data_afastamento) return '-';
            
            const data = new Date(registro.data_afastamento);
            const mes = data.toLocaleDateString('pt-BR', { month: 'short' });
            const ano = data.getFullYear();
            
            return `${mes}/${ano}`;
        }
    };
}

// ============ EXPORTAÇÃO ============

async function exportarDados() {
    try {
        const uploadId = document.getElementById('filtroUpload').value;
        let url = '/api/export/excel?client_id=1';
        if (uploadId) url += `&upload_id=${uploadId}`;
        
        window.location.href = url;
        
    } catch (error) {
        console.error('Erro ao exportar:', error);
        alert('Erro ao exportar dados');
    }
}

// ============ UTILITIES ============

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

// ============ MOSTRAR TODOS OS REGISTROS ============

function toggleMostrarTodos() {
    mostrarTodos = !mostrarTodos;
    const btn = document.getElementById('btnMostrarTodos');
    
    if (mostrarTodos) {
        registrosPorPagina = dadosFiltrados.length; // Mostra TODOS
        btn.innerHTML = '<i class="fas fa-compress"></i> Paginar';
        btn.style.background = 'var(--success)';
        btn.style.color = 'white';
    } else {
        registrosPorPagina = 100;
        btn.innerHTML = '<i class="fas fa-list"></i> Ver Todos';
        btn.style.background = '';
        btn.style.color = '';
    }
    
    paginaAtual = 1;
    renderizarTabela();
}

// ============ CRIAR COLUNA CUSTOMIZADA ============

function abrirModalNovaColuna() {
    document.getElementById('modalNovaColuna').classList.add('active');
}

function fecharModalNovaColuna() {
    document.getElementById('modalNovaColuna').classList.remove('active');
    document.getElementById('nomeNovaColuna').value = '';
    document.getElementById('formulaNovaColuna').value = '';
}

function preencherExemplo(tipo) {
    const textarea = document.getElementById('formulaNovaColuna');
    const nomeInput = document.getElementById('nomeNovaColuna');
    
    switch(tipo) {
        case 'primeiro_nome':
            nomeInput.value = 'Primeiro Nome';
            textarea.value = 'registro.nome_funcionario ? registro.nome_funcionario.split(\' \')[0] : \'-\'';
            break;
        case 'dias_em_horas':
            nomeInput.value = 'Dias em Horas';
            textarea.value = '(registro.dias_perdidos || 0) * 8';
            break;
        case 'categoria_duracao':
            nomeInput.value = 'Categoria Duração';
            textarea.value = `const dias = registro.dias_perdidos || 0;
if (dias <= 1) return 'Curto';
if (dias <= 7) return 'Médio';
return 'Longo';`;
            break;
    }
}

function criarColunaCustomizada() {
    const nome = document.getElementById('nomeNovaColuna').value.trim();
    const formula = document.getElementById('formulaNovaColuna').value.trim();
    
    if (!nome || !formula) {
        alert('❌ Preencha o nome e a fórmula da coluna!');
        return;
    }
    
    // Gera uma chave única
    const key = 'custom_' + nome.toLowerCase().replace(/\s+/g, '_');
    
    // Cria a função de cálculo
    let funcaoCalculo;
    try {
        funcaoCalculo = new Function('registro', `
            try {
                ${formula.includes('return') ? formula : 'return ' + formula}
            } catch (e) {
                return 'ERRO: ' + e.message;
            }
        `);
        
        // Testa com primeiro registro
        if (dadosCompletos.length > 0) {
            const teste = funcaoCalculo(dadosCompletos[0]);
            console.log('Teste da fórmula:', teste);
        }
        
    } catch (e) {
        alert('❌ Erro na fórmula:\n' + e.message);
        return;
    }
    
    // Adiciona a nova coluna
    colunasIA[key] = {
        visible: true,
        label: nome,
        type: 'text',
        sticky: false,
        ia: true,
        custom: true
    };
    
    // Calcula valores para todos os registros
    dadosCompletos.forEach(registro => {
        try {
            registro[key] = funcaoCalculo(registro);
        } catch (e) {
            registro[key] = 'ERRO';
        }
    });
    
    dadosFiltrados = [...dadosCompletos];
    
    renderizarTabela();
    renderizarGerenciadorColunas();
    fecharModalNovaColuna();
    
    alert(`✅ Coluna "${nome}" criada com sucesso!\n\nVocê pode:\n- Ver os valores na tabela\n- Filtrar por esta coluna\n- Gerenciar no painel de colunas`);
}

// ============ ESTILOS ADICIONAIS ============

// Adiciona estilo para botão sm
const style = document.createElement('style');
style.textContent = `
    .btn-sm {
        padding: 6px 12px;
        font-size: 12px;
        width: 100%;
    }
    
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 2000;
    }
    
    .modal-overlay.active {
        display: flex;
    }
    
    .search-box {
        position: relative;
    }
    
    .search-box i {
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        color: var(--text-secondary);
    }
    
    .search-box input {
        padding-left: 40px;
        width: 100%;
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 10px 10px 10px 40px;
    }
`;
document.head.appendChild(style);

// Fecha dropdowns ao clicar fora
document.addEventListener('click', () => {
    document.querySelectorAll('.filter-dropdown').forEach(d => d.classList.remove('active'));
});

