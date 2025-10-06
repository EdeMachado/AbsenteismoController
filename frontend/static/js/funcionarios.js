/**
 * Análise por Funcionários
 */

let funcionariosData = [];

document.addEventListener('DOMContentLoaded', () => {
    carregarFuncionarios();
    setupSearch();
});

async function carregarFuncionarios() {
    try {
        const response = await fetch('/api/analises/funcionarios?client_id=1');
        const data = await response.json();
        
        funcionariosData = data;
        renderizarFuncionarios(data);
        renderizarResumo(data);
        carregarSetores(data);
        
    } catch (error) {
        console.error('Erro:', error);
        document.getElementById('funcionariosTableBody').innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--danger);">
                    Erro ao carregar dados. Faça um upload primeiro.
                </td>
            </tr>
        `;
    }
}

function renderizarFuncionarios(dados) {
    const tbody = document.getElementById('funcionariosTableBody');
    
    if (dados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--text-secondary);">
                    Nenhum dado encontrado
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = dados.map(f => `
        <tr class="funcionario-row">
            <td><strong>${f.nome || 'Não informado'}</strong></td>
            <td>${f.setor || '-'}</td>
            <td>${f.genero || '-'}</td>
            <td style="font-weight: 600;">${f.quantidade}</td>
            <td>${Math.round(f.dias_perdidos)}</td>
            <td>${Math.round(f.horas_perdidas).toLocaleString('pt-BR')}</td>
            <td>${getBadge(f.quantidade)}</td>
        </tr>
    `).join('');
}

function renderizarResumo(dados) {
    const total = dados.length;
    const mediaAtestados = total > 0 ? (dados.reduce((acc, f) => acc + f.quantidade, 0) / total).toFixed(1) : 0;
    const mediaDias = total > 0 ? (dados.reduce((acc, f) => acc + f.dias_perdidos, 0) / total).toFixed(1) : 0;
    
    document.getElementById('totalFuncionarios').textContent = total;
    document.getElementById('mediaAtestados').textContent = mediaAtestados;
    document.getElementById('mediaDias').textContent = mediaDias;
}

function carregarSetores(dados) {
    const setores = [...new Set(dados.map(f => f.setor).filter(s => s))];
    const select = document.getElementById('filtroSetor');
    
    select.innerHTML = '<option value="">Todos</option>' + 
        setores.map(s => `<option value="${s}">${s}</option>`).join('');
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
    const searchInput = document.getElementById('searchFuncionario');
    searchInput.addEventListener('input', (e) => {
        const termo = e.target.value.toLowerCase();
        const filtrados = funcionariosData.filter(f => 
            (f.nome || '').toLowerCase().includes(termo)
        );
        renderizarFuncionarios(filtrados);
    });
}

function aplicarFiltrosFuncionarios() {
    const setor = document.getElementById('filtroSetor').value;
    const periodo = document.getElementById('filtroPeriodo').value;
    
    let url = '/api/analises/funcionarios?client_id=1';
    if (periodo) {
        url += `&mes_inicio=${periodo}&mes_fim=${periodo}`;
    }
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            funcionariosData = data;
            
            let filtrados = data;
            if (setor) {
                filtrados = data.filter(f => f.setor === setor);
            }
            
            renderizarFuncionarios(filtrados);
            renderizarResumo(filtrados);
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao aplicar filtros');
        });
}

function exportarExcel() {
    alert('Funcionalidade de export será implementada em breve!');
}
