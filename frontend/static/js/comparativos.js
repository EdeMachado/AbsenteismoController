/**
 * Comparativos - JavaScript
 */

let chartComparativo;

document.addEventListener('DOMContentLoaded', () => {
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (!clientId) {
        alert('Selecione um cliente na aba "Clientes" para visualizar os comparativos.');
        return;
    }
    carregarVisaoGeral(clientId);
    carregarSetores(clientId);
    carregarFaltas(clientId);
});

function setComparacao(tipo) {
    const hoje = new Date();
    let p1Inicio, p1Fim, p2Inicio, p2Fim;
    
    if (tipo === 'mensal') {
        // Mês atual vs mês anterior
        const mesAtual = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        const mesAnterior = new Date(hoje.getFullYear(), hoje.getMonth() - 1, 1);
        
        p2Inicio = p2Fim = formatMonth(mesAtual);
        p1Inicio = p1Fim = formatMonth(mesAnterior);
        
    } else if (tipo === 'trimestral') {
        // Último trimestre vs trimestre anterior
        const trim2Fim = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        const trim2Inicio = new Date(hoje.getFullYear(), hoje.getMonth() - 2, 1);
        const trim1Fim = new Date(hoje.getFullYear(), hoje.getMonth() - 3, 1);
        const trim1Inicio = new Date(hoje.getFullYear(), hoje.getMonth() - 5, 1);
        
        p2Inicio = formatMonth(trim2Inicio);
        p2Fim = formatMonth(trim2Fim);
        p1Inicio = formatMonth(trim1Inicio);
        p1Fim = formatMonth(trim1Fim);
        
    } else if (tipo === 'anual') {
        // Último ano vs ano anterior
        const ano2Fim = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        const ano2Inicio = new Date(hoje.getFullYear() - 1, hoje.getMonth() + 1, 1);
        const ano1Fim = new Date(hoje.getFullYear() - 1, hoje.getMonth(), 1);
        const ano1Inicio = new Date(hoje.getFullYear() - 2, hoje.getMonth() + 1, 1);
        
        p2Inicio = formatMonth(ano2Inicio);
        p2Fim = formatMonth(ano2Fim);
        p1Inicio = formatMonth(ano1Inicio);
        p1Fim = formatMonth(ano1Fim);
    }
    
    document.getElementById('periodo1Inicio').value = p1Inicio;
    document.getElementById('periodo1Fim').value = p1Fim;
    document.getElementById('periodo2Inicio').value = p2Inicio;
    document.getElementById('periodo2Fim').value = p2Fim;
}

async function compararPeriodos() {
    const p1Inicio = document.getElementById('periodo1Inicio').value;
    const p1Fim = document.getElementById('periodo1Fim').value;
    const p2Inicio = document.getElementById('periodo2Inicio').value;
    const p2Fim = document.getElementById('periodo2Fim').value;
    
    if (!p1Inicio || !p1Fim || !p2Inicio || !p2Fim) {
        alert('Preencha todos os períodos');
        return;
    }
    
    try {
        const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
        if (!clientId) {
            alert('Selecione um cliente para gerar o comparativo.');
            return;
        }
        const url = `/api/relatorios/comparativo?client_id=${clientId}&periodo1_inicio=${p1Inicio}&periodo1_fim=${p1Fim}&periodo2_inicio=${p2Inicio}&periodo2_fim=${p2Fim}`;
        const response = await fetch(url);
        const data = await response.json();
        
        renderizarComparacao(data);
        document.getElementById('resultadosComparativos').style.display = 'block';
        
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao gerar comparação. Verifique se existem dados para os períodos selecionados.');
    }
}

function renderizarComparacao(data) {
    // Período 1
    const p1Html = `
        <div style="display: grid; gap: 16px; margin-top: 16px;">
            <div>
                <div style="font-size: 12px; color: var(--text-secondary);">Atestados DIAS</div>
                <div style="font-size: 24px; font-weight: 700;">${data.periodo1.total_atestados_dias}</div>
            </div>
            <div>
                <div style="font-size: 12px; color: var(--text-secondary);">Atestados HORAS</div>
                <div style="font-size: 24px; font-weight: 700;">${data.periodo1.total_atestados_horas}</div>
            </div>
            <div>
                <div style="font-size: 12px; color: var(--text-secondary);">Dias Perdidos</div>
                <div style="font-size: 24px; font-weight: 700;">${Math.round(data.periodo1.total_dias_perdidos)}</div>
            </div>
            <div>
                <div style="font-size: 12px; color: var(--text-secondary);">Horas Perdidas</div>
                <div style="font-size: 24px; font-weight: 700;">${Math.round(data.periodo1.total_horas_perdidas).toLocaleString('pt-BR')}</div>
            </div>
        </div>
    `;
    
    // Período 2
    const p2Html = `
        <div style="display: grid; gap: 16px; margin-top: 16px;">
            <div>
                <div style="font-size: 12px; color: var(--text-secondary);">Atestados DIAS</div>
                <div style="font-size: 24px; font-weight: 700;">${data.periodo2.total_atestados_dias}</div>
            </div>
            <div>
                <div style="font-size: 12px; color: var(--text-secondary);">Atestados HORAS</div>
                <div style="font-size: 24px; font-weight: 700;">${data.periodo2.total_atestados_horas}</div>
            </div>
            <div>
                <div style="font-size: 12px; color: var(--text-secondary);">Dias Perdidos</div>
                <div style="font-size: 24px; font-weight: 700;">${Math.round(data.periodo2.total_dias_perdidos)}</div>
            </div>
            <div>
                <div style="font-size: 12px; color: var(--text-secondary);">Horas Perdidas</div>
                <div style="font-size: 24px; font-weight: 700;">${Math.round(data.periodo2.total_horas_perdidas).toLocaleString('pt-BR')}</div>
            </div>
        </div>
    `;
    
    document.getElementById('periodo1Cards').innerHTML = p1Html;
    document.getElementById('periodo2Cards').innerHTML = p2Html;
    
    // Variações
    const varHtml = `
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
            <div style="text-align: center; padding: 16px; background: var(--surface-hover); border-radius: 8px;">
                <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">Atestados</div>
                <div class="${getVariacaoClass(data.variacoes.atestados)}">
                    <i class="fas fa-${data.variacoes.atestados > 0 ? 'arrow-up' : 'arrow-down'}"></i>
                    ${Math.abs(data.variacoes.atestados).toFixed(1)}%
                </div>
            </div>
            <div style="text-align: center; padding: 16px; background: var(--surface-hover); border-radius: 8px;">
                <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">Dias</div>
                <div class="${getVariacaoClass(data.variacoes.dias)}">
                    <i class="fas fa-${data.variacoes.dias > 0 ? 'arrow-up' : 'arrow-down'}"></i>
                    ${Math.abs(data.variacoes.dias).toFixed(1)}%
                </div>
            </div>
            <div style="text-align: center; padding: 16px; background: var(--surface-hover); border-radius: 8px;">
                <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">Horas</div>
                <div class="${getVariacaoClass(data.variacoes.horas)}">
                    <i class="fas fa-${data.variacoes.horas > 0 ? 'arrow-up' : 'arrow-down'}"></i>
                    ${Math.abs(data.variacoes.horas).toFixed(1)}%
                </div>
            </div>
            <div style="text-align: center; padding: 16px; background: var(--surface-hover); border-radius: 8px;">
                <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">Taxa</div>
                <div class="${getVariacaoClass(data.variacoes.taxa)}">
                    <i class="fas fa-${data.variacoes.taxa > 0 ? 'arrow-up' : 'arrow-down'}"></i>
                    ${Math.abs(data.variacoes.taxa).toFixed(1)}%
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('variacoesDiv').innerHTML = varHtml;
    
    // Gráfico
    renderizarGraficoComparativo(data);
}

function renderizarGraficoComparativo(data) {
    const ctx = document.getElementById('chartComparativo');
    
    if (chartComparativo) chartComparativo.destroy();
    
    // Usa cores da empresa
    const CORES_EMPRESA = {
        primary: '#1a237e',  // Azul marinho
        secondary: '#6B8E23'  // Verde oliva
    };
    
    chartComparativo = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Total Atestados', 'Atestados (Dias)', 'Dias Perdidos', 'Horas Perdidas'],
            datasets: [
                {
                    label: `Período 1 (${data.periodo1.inicio} a ${data.periodo1.fim})`,
                    data: [
                        data.periodo1.total_atestados,
                        data.periodo1.total_atestados_dias,
                        Math.round(data.periodo1.total_dias_perdidos),
                        Math.round(data.periodo1.total_horas_perdidas)
                    ],
                    backgroundColor: CORES_EMPRESA.primary,
                    borderRadius: 6
                },
                {
                    label: `Período 2 (${data.periodo2.inicio} a ${data.periodo2.fim})`,
                    data: [
                        data.periodo2.total_atestados,
                        data.periodo2.total_atestados_dias,
                        Math.round(data.periodo2.total_dias_perdidos),
                        Math.round(data.periodo2.total_horas_perdidas)
                    ],
                    backgroundColor: CORES_EMPRESA.secondary,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        font: { size: 12 },
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                // Formata números grandes
                                if (context.parsed.y >= 1000) {
                                    label += context.parsed.y.toLocaleString('pt-BR');
                                } else {
                                    label += context.parsed.y;
                                }
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            if (value >= 1000) {
                                return value.toLocaleString('pt-BR');
                            }
                            return value;
                        }
                    }
                }
            }
        }
    });
}

function getVariacaoClass(valor) {
    return `variacao-badge ${valor > 0 ? 'variacao-positiva' : 'variacao-negativa'}`;
}

function formatMonth(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    return `${year}-${month}`;
}


