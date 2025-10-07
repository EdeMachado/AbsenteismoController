/**
 * Análise Completa de Dados - VERSÃO FINAL FUNCIONAL
 * Recursos: Scroll horizontal, Filtros por coluna, IA, Edição inline, Criar colunas
 */

// ========== VARIÁVEIS GLOBAIS ==========
let allData = [];
let filteredData = [];
let currentPage = 1;
let rowsPerPage = 100;
let showAll = false;
let activeFilters = {};

// Configuração de colunas padrão
let columns = {
    nome_funcionario: { visible: true, label: 'Funcionário', width: 'large', editable: true },
    cpf: { visible: true, label: 'CPF', width: 'medium', editable: true },
    matricula: { visible: true, label: 'Matrícula', width: 'small', editable: true },
    setor: { visible: true, label: 'Setor', width: 'medium', editable: true },
    cargo: { visible: true, label: 'Cargo', width: 'medium', editable: true },
    genero: { visible: true, label: 'Gênero', width: 'small', editable: true },
    data_afastamento: { visible: true, label: 'Data Afastamento', width: 'medium', editable: true },
    data_retorno: { visible: true, label: 'Data Retorno', width: 'medium', editable: true },
    tipo_info_atestado: { visible: true, label: 'Tipo', width: 'small', editable: false },
    tipo_atestado: { visible: true, label: 'Tipo Atestado', width: 'medium', editable: false },
    cid: { visible: true, label: 'CID', width: 'small', editable: true },
    descricao_cid: { visible: true, label: 'Descrição CID', width: 'xlarge', editable: true },
    numero_dias_atestado: { visible: true, label: 'Nº Dias', width: 'small', editable: true },
    numero_horas_atestado: { visible: true, label: 'Nº Horas', width: 'small', editable: true },
    dias_perdidos: { visible: true, label: 'Dias Perdidos', width: 'medium', editable: false },
    horas_perdidas: { visible: true, label: 'Horas Perdidas', width: 'medium', editable: false }
};

// Colunas criadas (IA ou customizadas)
let customColumns = {};

// ========== INICIALIZAÇÃO ==========
document.addEventListener('DOMContentLoaded', () => {
    loadUploads();
    loadData();
});

// ========== CARREGAR DADOS ==========
async function loadUploads() {
    try {
        const response = await fetch('/api/uploads?client_id=1');
        const uploads = await response.json();
        
        const select = document.getElementById('uploadSelect');
        select.innerHTML = '<option value="">Todos os uploads</option>' +
            uploads.map(u => `<option value="${u.id}">${u.filename}</option>`).join('');
        
    } catch (error) {
        console.error('Erro ao carregar uploads:', error);
    }
}

async function loadData() {
    try {
        const uploadId = document.getElementById('uploadSelect').value;
        let url = '/api/dados/todos?client_id=1';
        if (uploadId) url += `&upload_id=${uploadId}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        allData = data.dados || [];
        filteredData = [...allData];
        
        updateStats(data.estatisticas);
        renderTable();
        renderColumnManager();
        
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        alert('Erro ao carregar dados. Verifique se há uploads.');
    }
}

// ========== ESTATÍSTICAS ==========
function updateStats(stats) {
    document.getElementById('statTotal').textContent = (allData.length || 0).toLocaleString('pt-BR');
    
    const visibleCols = Object.values(columns).filter(c => c.visible).length + 
                        Object.values(customColumns).filter(c => c.visible).length;
    document.getElementById('statColunas').textContent = visibleCols;
    
    document.getElementById('statFiltrados').textContent = filteredData.length.toLocaleString('pt-BR');
    document.getElementById('statFiltros').textContent = Object.keys(activeFilters).length;
}

// ========== RENDERIZAR TABELA ==========
function renderTable() {
    const visibleColumns = Object.entries({...columns, ...customColumns})
        .filter(([key, config]) => config.visible);
    
    // Cabeçalho
    const thead = document.getElementById('tableHead');
    thead.innerHTML = `
        <tr>
            ${visibleColumns.map(([key, config]) => `
                <th class="col-${config.width || 'medium'}">
                    <div class="col-header">
                        <div class="col-title">
                            ${config.label}
                            ${config.isIA ? '<span class="badge badge-ia">IA</span>' : ''}
                        </div>
                        <button class="filter-btn ${activeFilters[key] ? 'active' : ''}" 
                                onclick="toggleFilter(event, '${key}')">
                            <i class="fas fa-filter"></i>
                        </button>
                        <div class="filter-dropdown" id="filter-${key}"></div>
                    </div>
                </th>
            `).join('')}
            <th class="col-small">Ações</th>
        </tr>
    `;
    
    // Corpo
    const start = (currentPage - 1) * rowsPerPage;
    const end = showAll ? filteredData.length : start + rowsPerPage;
    const pageData = filteredData.slice(start, end);
    
    const tbody = document.getElementById('tableBody');
    
    if (pageData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="${visibleColumns.length + 1}" style="text-align: center; padding: 60px; color: #999;">
                    <i class="fas fa-inbox" style="font-size: 48px; margin-bottom: 16px; display: block;"></i>
                    Nenhum registro encontrado
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = pageData.map((row, idx) => `
        <tr>
            ${visibleColumns.map(([key, config]) => {
                let value = row[key];
                let displayValue = formatValue(value, key);
                
                return `
                    <td class="${config.editable ? 'editable' : ''}" 
                        ondblclick="${config.editable ? `editCell(this, ${row.id}, '${key}')` : ''}">
                        ${displayValue}
                    </td>
                `;
            }).join('')}
            <td>
                <button class="btn btn-secondary btn-icon" onclick="deleteRow(${row.id})" title="Excluir">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    updateStats();
}

// ========== FORMATAÇÃO ==========
function formatValue(value, key) {
    if (value === null || value === undefined || value === '') return '-';
    
    if (key === 'cpf') {
        return value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
    
    if (key === 'data_afastamento' || key === 'data_retorno') {
        return new Date(value).toLocaleDateString('pt-BR');
    }
    
    if (key === 'tipo_info_atestado') {
        return value === 1 ? '<span class="badge badge-dias">Dias</span>' : 
               value === 3 ? '<span class="badge badge-horas">Horas</span>' : '-';
    }
    
    if (typeof value === 'number') {
        return value.toLocaleString('pt-BR', { maximumFractionDigits: 2 });
    }
    
    return value;
}

// ========== FILTROS POR COLUNA ==========
function toggleFilter(event, columnKey) {
    event.stopPropagation();
    
    const dropdown = document.getElementById(`filter-${columnKey}`);
    const allDropdowns = document.querySelectorAll('.filter-dropdown');
    
    // Fecha todos os outros
    allDropdowns.forEach(d => {
        if (d.id !== `filter-${columnKey}`) {
            d.classList.remove('show');
        }
    });
    
    // Toggle atual
    const isShow = dropdown.classList.toggle('show');
    
    if (isShow) {
        renderFilterOptions(columnKey);
    }
}

function renderFilterOptions(columnKey) {
    const dropdown = document.getElementById(`filter-${columnKey}`);
    
    // Pegar valores únicos
    const uniqueValues = [...new Set(allData.map(row => {
        let val = row[columnKey];
        if (val === null || val === undefined || val === '') return '(Vazio)';
        return String(val);
    }))].sort();
    
    const activeVals = activeFilters[columnKey] || [];
    
    dropdown.innerHTML = `
        <input type="text" class="filter-search" placeholder="Buscar valor..." 
               onkeyup="filterDropdownOptions('${columnKey}', this.value)" onclick="event.stopPropagation()">
        <div class="filter-options" id="filter-opts-${columnKey}">
            <div class="filter-option" onclick="selectAllFilter('${columnKey}', event)">
                <input type="checkbox" ${activeVals.length === 0 ? 'checked' : ''}>
                <span><strong>(Selecionar Todos)</strong></span>
            </div>
            ${uniqueValues.map(val => `
                <div class="filter-option" onclick="toggleFilterOption('${columnKey}', '${val.replace(/'/g, "\\'")}', event)">
                    <input type="checkbox" ${activeVals.length === 0 || activeVals.includes(val) ? 'checked' : ''}>
                    <span>${val}</span>
                </div>
            `).join('')}
        </div>
    `;
}

function toggleFilterOption(columnKey, value, event) {
    event.stopPropagation();
    
    if (!activeFilters[columnKey]) {
        activeFilters[columnKey] = [];
    }
    
    const idx = activeFilters[columnKey].indexOf(value);
    if (idx > -1) {
        activeFilters[columnKey].splice(idx, 1);
    } else {
        activeFilters[columnKey].push(value);
    }
    
    if (activeFilters[columnKey].length === 0) {
        delete activeFilters[columnKey];
    }
    
    applyFilters();
}

function selectAllFilter(columnKey, event) {
    event.stopPropagation();
    delete activeFilters[columnKey];
    applyFilters();
}

function applyFilters() {
    filteredData = allData.filter(row => {
        for (let [colKey, values] of Object.entries(activeFilters)) {
            if (values.length === 0) continue;
            
            let rowVal = row[colKey];
            if (rowVal === null || rowVal === undefined || rowVal === '') {
                rowVal = '(Vazio)';
            } else {
                rowVal = String(rowVal);
            }
            
            if (!values.includes(rowVal)) {
                return false;
            }
        }
        return true;
    });
    
    currentPage = 1;
    renderTable();
}

function clearAllFilters() {
    activeFilters = {};
    document.getElementById('searchBox').value = '';
    filteredData = [...allData];
    renderTable();
}

// ========== BUSCA GLOBAL ==========
function searchData() {
    const term = document.getElementById('searchBox').value.toLowerCase();
    
    if (!term) {
        filteredData = [...allData];
    } else {
        filteredData = allData.filter(row => {
            return Object.values(row).some(val => {
                if (val === null || val === undefined) return false;
                return String(val).toLowerCase().includes(term);
            });
        });
    }
    
    currentPage = 1;
    renderTable();
}

// ========== VER TODOS / PAGINAR ==========
function toggleShowAll() {
    showAll = !showAll;
    
    if (showAll) {
        document.getElementById('textShowAll').textContent = 'Paginar';
        document.getElementById('iconShowAll').className = 'fas fa-compress';
    } else {
        document.getElementById('textShowAll').textContent = 'Ver Todos';
        document.getElementById('iconShowAll').className = 'fas fa-list';
    }
    
    currentPage = 1;
    renderTable();
}

// ========== EDIÇÃO INLINE ==========
function editCell(cell, rowId, columnKey) {
    const currentValue = cell.textContent.trim();
    const originalValue = currentValue;
    
    // Cria input
    cell.innerHTML = `<input type="text" value="${currentValue}" onblur="saveCell(this, ${rowId}, '${columnKey}')" onkeypress="if(event.key==='Enter') this.blur()">`;
    
    // Foca no input
    const input = cell.querySelector('input');
    input.focus();
    input.select();
}

async function saveCell(input, rowId, columnKey) {
    const newValue = input.value;
    const cell = input.parentElement;
    
    try {
        // Atualiza no backend
        const response = await fetch(`/api/dados/${rowId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [columnKey]: newValue })
        });
        
        if (response.ok) {
            // Atualiza localmente
            const row = allData.find(r => r.id === rowId);
            if (row) row[columnKey] = newValue;
            
            cell.textContent = formatValue(newValue, columnKey);
            cell.style.background = '#c8e6c9';
            setTimeout(() => { cell.style.background = ''; }, 1000);
        } else {
            alert('Erro ao salvar');
            cell.textContent = formatValue(allData.find(r => r.id === rowId)[columnKey], columnKey);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar');
    }
}

async function deleteRow(rowId) {
    if (!confirm('Excluir este registro?')) return;
    
    try {
        const response = await fetch(`/api/dados/${rowId}`, { method: 'DELETE' });
        
        if (response.ok) {
            allData = allData.filter(r => r.id !== rowId);
            filteredData = filteredData.filter(r => r.id !== rowId);
            renderTable();
            alert('Registro excluído!');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao excluir');
    }
}

// ========== GERENCIAR COLUNAS ==========
function openColumnManager() {
    document.getElementById('columnPanel').classList.add('active');
    document.getElementById('overlay').classList.add('active');
    renderColumnManager();
}

function closeColumnManager() {
    document.getElementById('columnPanel').classList.remove('active');
    document.getElementById('overlay').classList.remove('active');
}

function renderColumnManager() {
    const list = document.getElementById('columnsList');
    const allColumns = {...columns, ...customColumns};
    
    list.innerHTML = Object.entries(allColumns).map(([key, config]) => `
        <div class="column-toggle">
            <input type="checkbox" ${config.visible ? 'checked' : ''} 
                   onchange="toggleColumnVisibility('${key}')">
            <span class="column-name">
                ${config.label}
                ${config.isIA ? '<span class="badge badge-ia">IA</span>' : ''}
            </span>
        </div>
    `).join('');
}

function toggleColumnVisibility(columnKey) {
    if (columns[columnKey]) {
        columns[columnKey].visible = !columns[columnKey].visible;
    } else if (customColumns[columnKey]) {
        customColumns[columnKey].visible = !customColumns[columnKey].visible;
    }
    
    renderTable();
    renderColumnManager();
}

// ========== CRIAR COLUNAS IA ==========
function createIAColumn(type) {
    let newColumn = null;
    
    switch(type) {
        case 'genero':
            newColumn = {
                key: 'ia_genero',
                label: 'Gênero (IA)',
                calculate: (row) => {
                    const nome = row.nome_funcionario || '';
                    const primeiroNome = nome.trim().split(' ')[0].toUpperCase();
                    return primeiroNome.endsWith('A') ? 'F' : 'M';
                }
            };
            break;
            
        case 'categoria_cid':
            newColumn = {
                key: 'ia_categoria_cid',
                label: 'Categoria CID (IA)',
                calculate: (row) => {
                    const categorias = {
                        'A': 'Infecciosas', 'B': 'Infecciosas', 'C': 'Neoplasias',
                        'D': 'Sangue', 'E': 'Endócrinas', 'F': 'Mentais',
                        'G': 'Nervoso', 'H': 'Olhos/Ouvidos', 'I': 'Circulatórias',
                        'J': 'Respiratórias', 'K': 'Digestivas', 'L': 'Pele',
                        'M': 'Musculoesqueléticas', 'N': 'Geniturinárias',
                        'O': 'Gravidez', 'R': 'Sintomas', 'S': 'Traumatismos',
                        'T': 'Envenenamentos', 'Z': 'Exames'
                    };
                    const letra = (row.cid || '').charAt(0).toUpperCase();
                    return categorias[letra] || 'Outros';
                }
            };
            break;
            
        case 'primeiro_nome':
            newColumn = {
                key: 'ia_primeiro_nome',
                label: 'Primeiro Nome (IA)',
                calculate: (row) => {
                    return (row.nome_funcionario || '').split(' ')[0];
                }
            };
            break;
            
        case 'mes_ano':
            newColumn = {
                key: 'ia_mes_ano',
                label: 'Mês/Ano (IA)',
                calculate: (row) => {
                    if (!row.data_afastamento) return '-';
                    const d = new Date(row.data_afastamento);
                    const meses = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
                    return `${meses[d.getMonth()]}/${d.getFullYear()}`;
                }
            };
            break;
    }
    
    if (newColumn) {
        // Calcula valores
        allData.forEach(row => {
            row[newColumn.key] = newColumn.calculate(row);
        });
        
        filteredData = [...allData];
        
        // Adiciona coluna
        customColumns[newColumn.key] = {
            visible: true,
            label: newColumn.label,
            width: 'medium',
            editable: false,
            isIA: true
        };
        
        renderTable();
        renderColumnManager();
        
        alert(`✅ Coluna "${newColumn.label}" criada com sucesso!\n\n${allData.length} registros processados.`);
    }
}

// ========== CRIAR COLUNA CUSTOMIZADA ==========
function openNewColumnModal() {
    document.getElementById('newColumnModal').classList.add('active');
    document.getElementById('overlay').classList.add('active');
}

function closeNewColumnModal() {
    document.getElementById('newColumnModal').classList.remove('active');
    if (!document.getElementById('columnPanel').classList.contains('active')) {
        document.getElementById('overlay').classList.remove('active');
    }
    document.getElementById('newColumnName').value = '';
    document.getElementById('newColumnFormula').value = '';
}

function fillExample(type) {
    const nameInput = document.getElementById('newColumnName');
    const formulaInput = document.getElementById('newColumnFormula');
    
    const examples = {
        'primeiro_nome': {
            name: 'Primeiro Nome',
            formula: 'registro.nome_funcionario ? registro.nome_funcionario.split(\' \')[0] : \'-\''
        },
        'ultimo_nome': {
            name: 'Último Nome',
            formula: 'const partes = registro.nome_funcionario.split(\' \');\nreturn partes[partes.length - 1];'
        },
        'categoria_duracao': {
            name: 'Categoria Duração',
            formula: 'const d = registro.dias_perdidos || 0;\nif (d <= 1) return \'Curto\';\nif (d <= 7) return \'Médio\';\nreturn \'Longo\';'
        },
        'dias_em_horas': {
            name: 'Total Horas',
            formula: '(registro.dias_perdidos || 0) * 8'
        }
    };
    
    const example = examples[type];
    if (example) {
        nameInput.value = example.name;
        formulaInput.value = example.formula;
    }
}

function createCustomColumn() {
    const name = document.getElementById('newColumnName').value.trim();
    const formula = document.getElementById('newColumnFormula').value.trim();
    
    if (!name || !formula) {
        alert('Preencha nome e fórmula!');
        return;
    }
    
    const key = 'custom_' + name.toLowerCase().replace(/\s+/g, '_');
    
    // Cria função
    let calcFunction;
    try {
        calcFunction = new Function('registro', `
            try {
                ${formula.includes('return') ? formula : 'return ' + formula}
            } catch (e) {
                return 'ERRO';
            }
        `);
        
        // Testa
        if (allData.length > 0) {
            const test = calcFunction(allData[0]);
            console.log('Teste:', test);
        }
    } catch (e) {
        alert('Erro na fórmula:\n' + e.message);
        return;
    }
    
    // Aplica a todos
    allData.forEach(row => {
        try {
            row[key] = calcFunction(row);
        } catch (e) {
            row[key] = 'ERRO';
        }
    });
    
    filteredData = [...allData];
    
    // Adiciona coluna
    customColumns[key] = {
        visible: true,
        label: name,
        width: 'medium',
        editable: false,
        isIA: true
    };
    
    renderTable();
    renderColumnManager();
    closeNewColumnModal();
    
    alert(`✅ Coluna "${name}" criada!\n\nProcessados ${allData.length} registros.`);
}

// ========== EXPORTAR ==========
function exportarExcel() {
    const uploadId = document.getElementById('uploadSelect').value;
    let url = '/api/export/excel?client_id=1';
    if (uploadId) url += `&upload_id=${uploadId}`;
    window.location.href = url;
}

// ========== FECHAR DROPDOWNS ==========
document.addEventListener('click', () => {
    document.querySelectorAll('.filter-dropdown').forEach(d => d.classList.remove('show'));
});

document.getElementById('overlay').addEventListener('click', () => {
    closeColumnManager();
    closeNewColumnModal();
});

