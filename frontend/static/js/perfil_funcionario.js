/**
 * Perfil de Funcionário
 */

let chartEvolucao, chartCids;
const CORES_EMPRESA = {
    primary: '#1a237e',
    secondary: '#6B8E23'
};

// Pega nome do funcionário da URL
function getNomeFuncionario() {
    const params = new URLSearchParams(window.location.search);
    return params.get('nome') || params.get('funcionario');
}

// Carrega dados do funcionário
async function carregarPerfil() {
    const nomeFuncionario = getNomeFuncionario();
    
    if (!nomeFuncionario) {
        alert('Nome do funcionário não especificado');
        window.location.href = '/funcionarios';
        return;
    }
    
    try {
        const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
        if (!clientId) {
            alert('Selecione um cliente na aba "Clientes" para acessar o perfil do funcionário.');
            return;
        }
        // Busca dados do funcionário
        const response = await fetch(`/api/funcionario/perfil?nome=${encodeURIComponent(nomeFuncionario)}&client_id=${clientId}`);
        
        if (!response.ok) {
            throw new Error('Erro ao carregar dados');
        }
        
        const data = await response.json();
        
        // Atualiza header
        document.getElementById('headerNome').textContent = `Perfil: ${data.nome}`;
        
        // Atualiza cards
        document.getElementById('totalAtestados').textContent = data.total_atestados || 0;
        document.getElementById('totalDias').textContent = Math.round(data.total_dias_perdidos || 0);
        document.getElementById('totalHoras').textContent = Math.round(data.total_horas_perdidas || 0);
        document.getElementById('mediaDias').textContent = data.media_dias_per_atestado ? data.media_dias_per_atestado.toFixed(1) : '0';
        
        // Atualiza informações
        document.getElementById('infoNome').textContent = data.nome || 'N/A';
        document.getElementById('infoSetor').textContent = data.setor || 'N/A';
        document.getElementById('infoGenero').textContent = data.genero === 'M' ? 'Masculino' : (data.genero === 'F' ? 'Feminino' : 'N/A');
        document.getElementById('infoTotalRegistros').textContent = data.total_registros || 0;
        
        // Renderiza gráficos
        renderizarGraficoEvolucao(data.evolucao_mensal || []);
        renderizarGraficoCids(data.top_cids || []);
        
        // Renderiza histórico
        renderizarHistorico(data.historico || []);
        
        // Mostra conteúdo
        document.getElementById('loading').style.display = 'none';
        document.getElementById('conteudo').style.display = 'block';
        
    } catch (error) {
        console.error('Erro:', error);
        document.getElementById('loading').innerHTML = `
            <div style="color: #c33;">
                <i class="fas fa-exclamation-triangle fa-3x"></i>
                <p style="margin-top: 16px;">Erro ao carregar dados do funcionário</p>
                <button class="btn btn-primary" onclick="window.location.href='/funcionarios'" style="margin-top: 16px;">
                    Voltar para Funcionários
                </button>
            </div>
        `;
    }
}

function renderizarGraficoEvolucao(dados) {
    const ctx = document.getElementById('chartEvolucao');
    if (!ctx) return;
    
    if (chartEvolucao) chartEvolucao.destroy();
    
    const labels = dados.map(d => {
        const mes = d.mes || '';
        return mes.split('-').reverse().join('/');
    });
    const valores = dados.map(d => d.dias_perdidos || 0);
    
    chartEvolucao = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Dias Perdidos',
                data: valores,
                borderColor: CORES_EMPRESA.primary,
                backgroundColor: 'rgba(26, 35, 126, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

function renderizarGraficoCids(dados) {
    const ctx = document.getElementById('chartCids');
    if (!ctx) return;
    
    if (chartCids) chartCids.destroy();
    
    const top5 = dados.slice(0, 5);
    const labels = top5.map(d => {
        const cid = d.cid || 'N/A';
        const desc = (d.descricao || d.diagnostico || '').substring(0, 30);
        return `${cid} - ${desc}`;
    });
    
    chartCids = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Quantidade',
                data: top5.map(d => d.quantidade || 0),
                backgroundColor: CORES_EMPRESA.secondary,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            const item = top5[index];
                            return `CID ${item.cid || 'N/A'}`;
                        },
                        label: function(context) {
                            const index = context.dataIndex;
                            const item = top5[index];
                            return [
                                `Diagnóstico: ${item.descricao || item.diagnostico || 'Não especificado'}`,
                                `Quantidade: ${item.quantidade || 0} atestados`,
                                `Dias perdidos: ${item.dias_perdidos || 0}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: { beginAtZero: true },
                y: { ticks: { font: { size: 11 } } }
            }
        }
    });
}

function renderizarHistorico(historico) {
    const tbody = document.getElementById('historicoTableBody');
    if (!tbody) return;
    
    if (historico.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum atestado encontrado</td></tr>';
        return;
    }
    
    tbody.innerHTML = historico.map(item => `
        <tr>
            <td>${item.data_afastamento || item.mes_referencia || 'N/A'}</td>
            <td>${item.cid || 'N/A'}</td>
            <td>${(item.diagnostico || item.descricao || 'N/A').substring(0, 50)}</td>
            <td>${item.dias_atestados || 0}</td>
            <td>${item.horas_perdi || 0}</td>
            <td>${item.motivo_atestado || 'N/A'}</td>
            <td>${item.setor || 'N/A'}</td>
        </tr>
    `).join('');
}

// Inicialização
document.addEventListener('DOMContentLoaded', async () => {
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (!clientId) {
        alert('Selecione um cliente na aba "Clientes" para acessar o perfil do funcionário.');
        return;
    }
    await carregarPerfil();
});

