/**
 * Análise de Dados - Estilo PowerBI
 * Interface simples e intuitiva
 */

let allData = [];
let filteredData = [];
let activeFilters = {};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setupEventListeners();
});

// Carregar dados
async function loadData() {
    try {
        // Verifica se há upload_id na URL
        const urlParams = new URLSearchParams(window.location.search);
        const uploadId = urlParams.get('upload_id');
        
        let url = '/api/dados/todos?client_id=1';
        if (uploadId) {
            url += `&upload_id=${uploadId}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        allData = data.dados || [];
        filteredData = [...allData];
        
        updateStats();
        renderTable();
        
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        showError('Erro ao carregar dados');
    }
}

// Configurar eventos
function setupEventListeners() {
    // Busca global
    document.getElementById('searchBox').addEventListener('input', (e) => {
        searchData(e.target.value);
    });
    
    // Navegação por teclado
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return;
        
        const activeCell = document.querySelector('.cell-focused');
        if (!activeCell) return;
        
        switch(e.key) {
            case 'ArrowRight':
                e.preventDefault();
                navigateToNextCell(activeCell);
                break;
            case 'ArrowLeft':
                e.preventDefault();
                navigateToPreviousCell(activeCell);
                break;
            case 'ArrowDown':
                e.preventDefault();
                navigateToNextRow(activeCell);
                break;
            case 'ArrowUp':
                e.preventDefault();
                navigateToPreviousRow(activeCell);
                break;
            case 'Enter':
                e.preventDefault();
                if (activeCell.classList.contains('editable')) {
                    editCell(activeCell);
                }
                break;
            case 'Home':
                e.preventDefault();
                navigateToFirstCell();
                break;
            case 'End':
                e.preventDefault();
                navigateToLastCell();
                break;
        }
    });
    
    // Clique para focar célula
    document.addEventListener('click', (e) => {
        if (e.target.tagName === 'TD') {
            focusCell(e.target);
        }
    });
}

// Renderizar tabela
function renderTable() {
    const tbody = document.getElementById('tableBody');
    
    if (filteredData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="12" style="text-align: center; padding: 40px;">
                    <i class="fas fa-inbox"></i> Nenhum registro encontrado
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = filteredData.map(row => `
        <tr>
            <td>${row.id || '-'}</td>
            <td class="editable" data-field="nome_funcionario" data-id="${row.id}">${row.nome_funcionario || '-'}</td>
            <td class="editable" data-field="cpf" data-id="${row.id}">${formatCPF(row.cpf) || '-'}</td>
            <td class="editable" data-field="setor" data-id="${row.id}">${row.setor || '-'}</td>
            <td class="editable" data-field="genero" data-id="${row.id}">${row.genero || '-'}</td>
            <td>${formatDate(row.data_afastamento) || '-'}</td>
            <td>${formatDate(row.data_retorno) || '-'}</td>
            <td>${formatTipo(row.tipo_info_atestado) || '-'}</td>
            <td class="editable" data-field="cid" data-id="${row.id}">${row.cid || '-'}</td>
            <td class="editable" data-field="descricao_cid" data-id="${row.id}">${row.descricao_cid || '-'}</td>
            <td>${row.numero_dias_atestado || '-'}</td>
            <td>${row.numero_horas_atestado || '-'}</td>
        </tr>
    `).join('');
    
    // Foca na primeira célula editável
    setTimeout(() => {
        const firstEditable = document.querySelector('td.editable');
        if (firstEditable) {
            focusCell(firstEditable);
        }
    }, 100);
}

// Focar célula
function focusCell(cell) {
    document.querySelectorAll('.cell-focused').forEach(c => {
        c.classList.remove('cell-focused');
    });
    cell.classList.add('cell-focused');
}

// Navegação
function navigateToNextCell(currentCell) {
    const nextCell = currentCell.nextElementSibling;
    if (nextCell) {
        focusCell(nextCell);
        scrollToCell(nextCell);
    } else {
        const nextRow = currentCell.parentElement.nextElementSibling;
        if (nextRow) {
            const firstCell = nextRow.querySelector('td');
            if (firstCell) {
                focusCell(firstCell);
                scrollToCell(firstCell);
            }
        }
    }
}

function navigateToPreviousCell(currentCell) {
    const prevCell = currentCell.previousElementSibling;
    if (prevCell) {
        focusCell(prevCell);
        scrollToCell(prevCell);
    } else {
        const prevRow = currentCell.parentElement.previousElementSibling;
        if (prevRow) {
            const lastCell = prevRow.querySelector('td:last-child');
            if (lastCell) {
                focusCell(lastCell);
                scrollToCell(lastCell);
            }
        }
    }
}

function navigateToNextRow(currentCell) {
    const currentRow = currentCell.parentElement;
    const nextRow = currentRow.nextElementSibling;
    if (nextRow) {
        const cellIndex = Array.from(currentRow.children).indexOf(currentCell);
        const nextCell = nextRow.children[cellIndex];
        if (nextCell) {
            focusCell(nextCell);
            scrollToCell(nextCell);
        }
    }
}

function navigateToPreviousRow(currentCell) {
    const currentRow = currentCell.parentElement;
    const prevRow = currentRow.previousElementSibling;
    if (prevRow) {
        const cellIndex = Array.from(currentRow.children).indexOf(currentCell);
        const prevCell = prevRow.children[cellIndex];
        if (prevCell) {
            focusCell(prevCell);
            scrollToCell(prevCell);
        }
    }
}

// Função para rolar até a célula
function scrollToCell(cell) {
    const tableContainer = document.querySelector('.table-container');
    const cellRect = cell.getBoundingClientRect();
    const containerRect = tableContainer.getBoundingClientRect();
    
    // Scroll horizontal
    if (cellRect.left < containerRect.left) {
        tableContainer.scrollLeft -= (containerRect.left - cellRect.left + 20);
    } else if (cellRect.right > containerRect.right) {
        tableContainer.scrollLeft += (cellRect.right - containerRect.right + 20);
    }
    
    // Scroll vertical
    if (cellRect.top < containerRect.top) {
        tableContainer.scrollTop -= (containerRect.top - cellRect.top + 20);
    } else if (cellRect.bottom > containerRect.bottom) {
        tableContainer.scrollTop += (cellRect.bottom - containerRect.bottom + 20);
    }
}

// Navegar para primeira célula
function navigateToFirstCell() {
    const firstCell = document.querySelector('td');
    if (firstCell) {
        focusCell(firstCell);
        scrollToCell(firstCell);
    }
}

// Navegar para última célula
function navigateToLastCell() {
    const lastCell = document.querySelector('td:last-child');
    if (lastCell) {
        focusCell(lastCell);
        scrollToCell(lastCell);
    }
}

// Editar célula
function editCell(cell) {
    const field = cell.dataset.field;
    const id = cell.dataset.id;
    const currentValue = cell.textContent.trim();
    
    cell.innerHTML = `<input type="text" value="${currentValue}" onblur="saveCell(this, '${field}', ${id})" onkeypress="if(event.key==='Enter') this.blur()">`;
    
    const input = cell.querySelector('input');
    input.focus();
    input.select();
}

// Salvar célula
async function saveCell(input, field, id) {
    const newValue = input.value;
    const cell = input.parentElement;
    
    try {
        const response = await fetch(`/api/dados/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [field]: newValue })
        });
        
        if (response.ok) {
            // Atualiza localmente
            const row = allData.find(r => r.id === id);
            if (row) row[field] = newValue;
            
            cell.textContent = formatValue(newValue, field);
            cell.style.background = '#d4edda';
            setTimeout(() => { cell.style.background = ''; }, 1000);
            
            // Reaplica filtros
            applyFilters();
        } else {
            alert('Erro ao salvar');
            cell.textContent = formatValue(allData.find(r => r.id === id)[field], field);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar');
    }
}

// Buscar dados
function searchData(term) {
    if (!term) {
        filteredData = [...allData];
    } else {
        filteredData = allData.filter(row => {
            return Object.values(row).some(val => {
                if (val === null || val === undefined) return false;
                return String(val).toLowerCase().includes(term.toLowerCase());
            });
        });
    }
    
    updateStats();
    renderTable();
}

// Limpar filtros
function clearFilters() {
    document.getElementById('searchBox').value = '';
    activeFilters = {};
    filteredData = [...allData];
    updateStats();
    renderTable();
}

// Atualizar estatísticas
function updateStats() {
    document.getElementById('totalRecords').textContent = allData.length.toLocaleString('pt-BR');
    document.getElementById('filteredRecords').textContent = filteredData.length.toLocaleString('pt-BR');
    document.getElementById('activeFilters').textContent = Object.keys(activeFilters).length;
}

// Aplicar filtros
function applyFilters() {
    filteredData = allData.filter(row => {
        for (let [field, values] of Object.entries(activeFilters)) {
            if (values.length === 0) continue;
            
            let rowVal = row[field];
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
    
    updateStats();
    renderTable();
}

// Exportar dados
function exportData() {
    const data = filteredData.map(row => ({
        'ID': row.id,
        'Funcionário': row.nome_funcionario,
        'CPF': row.cpf,
        'Setor': row.setor,
        'Gênero': row.genero,
        'Data Afastamento': row.data_afastamento,
        'Data Retorno': row.data_retorno,
        'Tipo': formatTipo(row.tipo_info_atestado),
        'CID': row.cid,
        'Descrição CID': row.descricao_cid,
        'Dias': row.numero_dias_atestado,
        'Horas': row.numero_horas_atestado
    }));
    
    const csv = convertToCSV(data);
    downloadCSV(csv, 'dados_atestados.csv');
}

// Função melhorada para detectar gênero
function detectarGenero(nome) {
    if (!nome || typeof nome !== 'string') return 'Indefinido';
    
    const nomeLimpo = nome.toLowerCase().trim();
    
    // Nomes femininos comuns no Brasil
    const nomesFemininos = [
        'ana', 'maria', 'joana', 'carla', 'patricia', 'sandra', 'lucia', 'rita', 'rosa', 'elena',
        'fernanda', 'juliana', 'camila', 'bruna', 'leticia', 'vanessa', 'daniela', 'cristina',
        'adriana', 'silvia', 'monica', 'fabiana', 'alessandra', 'andrea', 'claudia', 'denise',
        'eliane', 'fatima', 'gabriela', 'helena', 'isabel', 'jessica', 'karen', 'luciana',
        'marcia', 'natalia', 'olivia', 'paula', 'quenia', 'renata', 'sabrina', 'tatiana',
        'ursula', 'vera', 'wanda', 'yara', 'zilda', 'beatriz', 'carolina', 'diana', 'elisa',
        'flavia', 'gisele', 'hilda', 'iris', 'julia', 'kelly', 'laura', 'marta', 'nina',
        'otilia', 'priscila', 'raquel', 'sara', 'teresa', 'valeria', 'wilma', 'yasmin'
    ];
    
    // Nomes masculinos comuns no Brasil
    const nomesMasculinos = [
        'joao', 'jose', 'antonio', 'francisco', 'carlos', 'paulo', 'pedro', 'lucas', 'luiz',
        'marcos', 'luis', 'gabriel', 'rafael', 'daniel', 'marcelo', 'bruno', 'eduardo',
        'felipe', 'ricardo', 'roberto', 'fernando', 'thiago', 'joaquim', 'guilherme', 'gustavo',
        'rodrigo', 'sergio', 'fabio', 'andre', 'alexandre', 'leonardo', 'vinicius', 'diego',
        'miguel', 'arthur', 'bernardo', 'heitor', 'davi', 'lorenzo', 'theo', 'noah', 'benjamin',
        'samuel', 'enzo', 'joaquim', 'murilo', 'matheus', 'isaac', 'anthony', 'ryan', 'bryan',
        'caio', 'enzo', 'levi', 'henrique', 'lucca', 'nicolas', 'joao miguel', 'pedro henrique',
        'cauã', 'bento', 'antonio', 'vitor', 'emanuel', 'davi lucca', 'benicio', 'augusto',
        'joão gabriel', 'pietro', 'cauê', 'enzo gabriel', 'joão pedro', 'theo', 'anthony gabriel'
    ];
    
    // Primeiro nome (antes do espaço)
    const primeiroNome = nomeLimpo.split(' ')[0];
    
    // Verifica se é nome feminino conhecido
    if (nomesFemininos.includes(primeiroNome)) {
        return 'Feminino';
    }
    
    // Verifica se é nome masculino conhecido
    if (nomesMasculinos.includes(primeiroNome)) {
        return 'Masculino';
    }
    
    // Regras por terminação (mais confiável)
    const terminacoesFemininas = ['a', 'ia', 'ina', 'ana', 'ena', 'ela', 'ila', 'ola', 'ula'];
    const terminacoesMasculinas = ['o', 'io', 'ao', 'eo', 'uo', 'os', 'us', 'es', 'is'];
    
    // Verifica terminação feminina
    for (const term of terminacoesFemininas) {
        if (primeiroNome.endsWith(term)) {
            return 'Feminino';
        }
    }
    
    // Verifica terminação masculina
    for (const term of terminacoesMasculinas) {
        if (primeiroNome.endsWith(term)) {
            return 'Masculino';
        }
    }
    
    // Se não conseguiu determinar, retorna indefinido
    return 'Indefinido';
}

// Detectar gêneros automaticamente
async function detectarGeneros() {
    const botao = document.querySelector('button[onclick="detectarGeneros()"]');
    const textoOriginal = botao.innerHTML;
    
    botao.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detectando...';
    botao.disabled = true;
    
    let atualizados = 0;
    let erros = 0;
    
    for (let i = 0; i < allData.length; i++) {
        const registro = allData[i];
        const nome = registro.nome_funcionario;
        
        if (nome && (!registro.genero || registro.genero === 'Indefinido')) {
            const generoDetectado = detectarGenero(nome);
            
            if (generoDetectado !== 'Indefinido') {
                try {
                    const response = await fetch(`/api/dados/${registro.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ genero: generoDetectado })
                    });
                    
                    if (response.ok) {
                        registro.genero = generoDetectado;
                        atualizados++;
                    } else {
                        erros++;
                    }
                } catch (error) {
                    erros++;
                }
            }
        }
        
        // Atualiza progresso a cada 10 registros
        if (i % 10 === 0) {
            botao.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Detectando... ${i}/${allData.length}`;
        }
    }
    
    // Reaplica filtros e atualiza tabela
    applyFilters();
    
    // Restaura botão
    botao.innerHTML = textoOriginal;
    botao.disabled = false;
    
    // Mostra resultado
    alert(`✅ Detecção concluída!\n\n📊 Resultados:\n• ${atualizados} gêneros detectados\n• ${erros} erros\n• ${allData.length - atualizados - erros} já tinham gênero definido`);
}

// Funções auxiliares
function formatCPF(cpf) {
    if (!cpf) return '';
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

function formatDate(date) {
    if (!date) return '';
    return new Date(date).toLocaleDateString('pt-BR');
}

function formatTipo(tipo) {
    if (tipo === 1) return 'Dias';
    if (tipo === 3) return 'Horas';
    return '';
}

function formatValue(value, field) {
    if (field === 'cpf') return formatCPF(value);
    if (field === 'data_afastamento' || field === 'data_retorno') return formatDate(value);
    return value || '-';
}

function convertToCSV(data) {
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n');
    
    return csvContent;
}

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function showError(message) {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="11" style="text-align: center; padding: 40px; color: #dc3545;">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </td>
        </tr>
    `;
}
